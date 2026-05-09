"""
Meeting Room Booking System — FastAPI Backend (Cloud Optimized)
"""

from __future__ import annotations
import os
import json
from datetime import datetime, date, timedelta
from typing import List, Optional

import pymysql
import pymysql.cursors
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dbutils.pooled_db import PooledDB # 📌 อย่าลืมเพิ่ม dbutils ใน requirements.txt

# ─────────────────────────────────────────────
#  DATABASE CONNECTION POOL SETUP (Cloud Optimized)
# ─────────────────────────────────────────────
# สร้าง Pool ทิ้งไว้เพื่อลดเวลาในการทำ SSL Handshake กับ TiDB Cloud ทุกรอบ
pool = PooledDB(
    creator=pymysql,
    maxconnections=10,    # รองรับการเชื่อมต่อพร้อมกันมากขึ้น
    mincached=2,          # สแตนด์บายรอไว้ 2 ท่อเสมอ
    maxcached=5,          
    ping=2,               # 📌 ตรวจสอบความพร้อมของท่อก่อนส่งข้อมูล (กันท่อหลุด)
    host=os.environ.get('DB_HOST', 'localhost'),
    port=int(os.environ.get('DB_PORT', 4000)),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', ''),
    database=os.environ.get('DB_DATABASE', 'test'),
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
    # 📌 บังคับใช้ SSL ตลอดเวลาสำหรับ TiDB Cloud
    ssl={'ssl_verify_cert': True, 'ssl_verify_identity': True}
)

def get_conn():
    """ดึงท่อที่มีอยู่จาก Pool มาใช้ (ความเร็วสูงกว่าการต่อใหม่)"""
    return pool.connection()

# ─────────────────────────────────────────────
#  APP INITIALIZATION
# ─────────────────────────────────────────────
app = FastAPI(title="Meeting Room Booking API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📌 ให้ Render รับรู้ไฟล์ Static (index.html) ในที่เดียวกับ main.py
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/", include_in_schema=False)
def root():
    return FileResponse("index.html")

# ─────────────────────────────────────────────
#  PYDANTIC MODELS
# ─────────────────────────────────────────────
class BookingCreate(BaseModel):
    user_id:        int
    room_id:        int
    title:          str
    start_datetime: str   
    end_datetime:   str
    require_break:  bool = False
    break_note:     Optional[str] = ""
    note:           Optional[str] = ""
    attendee_emails: List[str] = []
    equipment_ids:  List[int] = []

class RoomUpdate(BaseModel):
    room_name: Optional[str] = None
    capacity: Optional[int] = None
    location_floor: Optional[str] = None

class EquipmentCreate(BaseModel):
    name: str
    type: str
    room_id: Optional[int] = None
    is_room_fixed: bool = False
    status: str = "available"
    description: Optional[str] = ""

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    room_id: Optional[int] = None
    is_room_fixed: Optional[bool] = None
    status: Optional[str] = None
    description: Optional[str] = None

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def _serialize(row: dict) -> dict:
    for k, v in row.items():
        if isinstance(v, (datetime, date)):
            row[k] = v.isoformat()
    return row

# ─────────────────────────────────────────────
#  ENDPOINTS
# ─────────────────────────────────────────────

# ---------- ROOMS ----------
@app.get("/api/rooms")
def list_rooms():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM room ORDER BY capacity DESC")
            rooms = cur.fetchall()
            for room in rooms:
                _serialize(room)
                cur.execute(
                    "SELECT equipment_id, name, type, status FROM equipment WHERE room_id = %s AND is_room_fixed = TRUE",
                    (room["room_id"],),
                )
                room["equipment"] = cur.fetchall()
        return {"rooms": rooms}
    finally:
        conn.close()

@app.get("/api/rooms/availability")
def rooms_availability(check_date: str = Query(...), start_time: str = Query("08:00"), end_time: str = Query("17:00")):
    try:
        start_dt = datetime.strptime(f"{check_date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt   = datetime.strptime(f"{check_date} {end_time}",   "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date/time format")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM room ORDER BY capacity DESC")
            rooms = cur.fetchall()
            for room in rooms:
                _serialize(room)
                cur.execute(
                    """SELECT booking_id, title, start_datetime, end_datetime, status FROM booking 
                       WHERE room_id = %s AND status IN ('confirmed','pending') 
                       AND start_datetime < %s AND end_datetime > %s ORDER BY start_datetime""",
                    (room["room_id"], end_dt, start_dt),
                )
                conflicts = cur.fetchall()
                for c in conflicts: _serialize(c)
                room["is_available"] = len(conflicts) == 0
                room["conflicts"]    = conflicts
                cur.execute("SELECT name, type, status FROM equipment WHERE room_id=%s AND is_room_fixed=TRUE", (room["room_id"],))
                room["equipment"] = cur.fetchall()
        return {"rooms": rooms}
    finally:
        conn.close()

@app.patch("/api/rooms/{room_id}")
def update_room(room_id: int, payload: RoomUpdate):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            fields = []
            values = []
            for k, v in payload.dict(exclude_unset=True).items():
                fields.append(f"{k}=%s")
                values.append(v)
            if not fields: return {"message": "No changes"}
            values.append(room_id)
            cur.execute(f"UPDATE room SET {', '.join(fields)} WHERE room_id=%s", tuple(values))
        conn.commit()
        return {"message": "อัปเดตห้องสำเร็จ"}
    finally:
        conn.close()

# ---------- EQUIPMENT ----------
@app.get("/api/equipment")
def list_equipment(shared_only: bool = False):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if shared_only:
                cur.execute("SELECT * FROM equipment WHERE is_room_fixed=FALSE ORDER BY type, name")
            else:
                cur.execute("SELECT * FROM equipment ORDER BY is_room_fixed DESC, type, name")
            items = cur.fetchall()
            for i in items: _serialize(i)
        return {"equipment": items}
    finally:
        conn.close()

@app.post("/api/equipment", status_code=201)
def create_equipment(payload: EquipmentCreate):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO equipment (room_id, name, type, is_room_fixed, status, description)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (payload.room_id, payload.name, payload.type, payload.is_room_fixed, payload.status, payload.description)
            )
        conn.commit()
        return {"message": "เพิ่มอุปกรณ์สำเร็จ"}
    finally:
        conn.close()

@app.patch("/api/equipment/{equipment_id}")
def update_equipment(equipment_id: int, payload: EquipmentUpdate):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            fields = []
            values = []
            for k, v in payload.dict(exclude_unset=True).items():
                fields.append(f"{k}=%s")
                values.append(v)
            if not fields: return {"message": "No changes"}
            values.append(equipment_id)
            cur.execute(f"UPDATE equipment SET {', '.join(fields)} WHERE equipment_id=%s", tuple(values))
        conn.commit()
        return {"message": "อัปเดตสำเร็จ"}
    finally:
        conn.close()

@app.delete("/api/equipment/{equipment_id}")
def delete_equipment(equipment_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM booking_equipment WHERE equipment_id=%s", (equipment_id,))
            cur.execute("DELETE FROM equipment WHERE equipment_id=%s", (equipment_id,))
        conn.commit()
        return {"message": "ลบสำเร็จ"}
    finally:
        conn.close()

# ---------- BOOKINGS ----------
@app.get("/api/bookings")
def list_bookings(user_id: Optional[int] = None, room_id: Optional[int] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, status: Optional[str] = None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = """SELECT b.*, u.full_name AS booker_name, u.department, r.room_name, r.capacity, r.location_floor
                     FROM booking b JOIN user u ON b.user_id = u.user_id JOIN room r ON b.room_id = r.room_id WHERE 1=1"""
            params = []
            if user_id: sql += " AND b.user_id = %s"; params.append(user_id)
            if room_id: sql += " AND b.room_id = %s"; params.append(room_id)
            if status: sql += " AND b.status = %s"; params.append(status)
            if date_from: sql += " AND DATE(b.start_datetime) >= %s"; params.append(date_from)
            if date_to: sql += " AND DATE(b.start_datetime) <= %s"; params.append(date_to)
            sql += " ORDER BY b.start_datetime"

            cur.execute(sql, params)
            bookings = cur.fetchall()
            for bk in bookings:
                _serialize(bk)
                cur.execute("SELECT * FROM booking_attendee WHERE booking_id=%s", (bk["booking_id"],))
                bk["attendees"] = cur.fetchall()
                cur.execute("""
                    SELECT e.equipment_id, e.name, e.type 
                    FROM booking_equipment be JOIN equipment e ON be.equipment_id = e.equipment_id
                    WHERE be.booking_id = %s
                """, (bk["booking_id"],))
                bk["equipment"] = cur.fetchall()
        return {"bookings": bookings}
    finally:
        conn.close()

@app.post("/api/bookings", status_code=201)
def create_booking(payload: BookingCreate):
    try:
        start_dt = datetime.strptime(payload.start_datetime, "%Y-%m-%d %H:%M:%S")
        end_dt   = datetime.strptime(payload.end_datetime,   "%Y-%m-%d %H:%M:%S")
    except ValueError: raise HTTPException(status_code=422, detail="Datetime error")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT booking_id FROM booking WHERE room_id = %s AND status IN ('confirmed','pending') AND start_datetime < %s AND end_datetime > %s",
                        (payload.room_id, end_dt, start_dt))
            if cur.fetchone(): raise HTTPException(status_code=409, detail="ห้องถูกจองแล้วเวลานี้")

            cur.execute("""INSERT INTO booking (user_id, room_id, title, start_datetime, end_datetime, status, require_break, break_note, note)
                           VALUES (%s,%s,%s,%s,%s,'confirmed',%s,%s,%s)""",
                        (payload.user_id, payload.room_id, payload.title, start_dt, end_dt, payload.require_break, payload.break_note, payload.note))
            booking_id = cur.lastrowid

            for email in payload.attendee_emails:
                if email.strip():
                    cur.execute("INSERT INTO booking_attendee (booking_id, email) VALUES (%s,%s)", (booking_id, email.strip()))
            for eq_id in payload.equipment_ids:
                cur.execute("INSERT INTO booking_equipment (booking_id, equipment_id) VALUES (%s,%s)", (booking_id, eq_id))
        conn.commit()
        return {"booking_id": booking_id, "status": "confirmed"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.patch("/api/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE booking SET status='cancelled' WHERE booking_id=%s", (booking_id,))
        conn.commit()
        return {"status": "cancelled"}
    finally:
        conn.close()

# ---------- STATS ----------
@app.get("/api/stats/dashboard")
def dashboard_stats():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            today = date.today()
            now = datetime.now()
            cur.execute("SELECT COUNT(*) AS cnt FROM room")
            total_rooms = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) AS cnt FROM booking WHERE DATE(start_datetime) = %s AND status != 'cancelled'", (today,))
            today_bookings = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(DISTINCT room_id) AS cnt FROM booking WHERE status IN ('confirmed','pending') AND start_datetime <= %s AND end_datetime >= %s", (now, now))
            available_now = total_rooms - cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) AS cnt FROM booking WHERE DATE(start_datetime) >= %s AND status != 'cancelled'", (today.replace(day=1),))
            month_bookings = cur.fetchone()["cnt"]
        return {"total_rooms": total_rooms, "available_now": available_now, "today_bookings": today_bookings, "month_bookings": month_bookings}
    finally:
        conn.close()

@app.get("/api/stats/room_usage")
def room_usage():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            month_start = date.today().replace(day=1)
            cur.execute("""SELECT r.room_id, r.room_name, r.capacity, COUNT(b.booking_id) AS booking_count,
                           ROUND(SUM(TIMESTAMPDIFF(MINUTE, b.start_datetime, b.end_datetime)) / 60.0, 1) AS hours_used
                           FROM room r LEFT JOIN booking b ON b.room_id = r.room_id AND DATE(b.start_datetime) >= %s AND b.status != 'cancelled'
                           GROUP BY r.room_id ORDER BY r.capacity DESC""", (month_start,))
            rows = cur.fetchall()
            for r in rows:
                r["hours_used"] = float(r["hours_used"] or 0)
                r["usage_percent"] = round(min(r["hours_used"] / 180 * 100, 100), 1)
        return {"usage": rows}
    finally:
        conn.close()