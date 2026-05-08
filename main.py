"""
Meeting Room Booking System — FastAPI Backend
Run with: uvicorn main:app --host 0.0.0.0 --port 8080 --reload
"""

from __future__ import annotations

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

# ─────────────────────────────────────────────
#  DB CONFIG  — update password if needed
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",  # เติมรหัสผ่าน AppServ ตรงนี้ถ้ามี
    "database": "meeting_room_db",
    "charset":  "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

def get_conn():
    return pymysql.connect(**DB_CONFIG)

# ─────────────────────────────────────────────
#  APP
# ─────────────────────────────────────────────
app = FastAPI(title="Meeting Room Booking API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class BookingCancel(BaseModel):
    booking_id: int

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

# โมเดลใหม่สำหรับแก้ไขห้องประชุม
class RoomUpdate(BaseModel):
    room_name: Optional[str] = None
    capacity: Optional[int] = None
    location_floor: Optional[str] = None

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
            cur.execute("SELECT * FROM Room ORDER BY capacity DESC")
            rooms = cur.fetchall()
            for room in rooms:
                _serialize(room)
                cur.execute(
                    "SELECT equipment_id, name, type, status FROM Equipment WHERE room_id = %s AND is_room_fixed = TRUE",
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
            cur.execute("SELECT * FROM Room ORDER BY capacity DESC")
            rooms = cur.fetchall()
            for room in rooms:
                _serialize(room)
                cur.execute(
                    """SELECT booking_id, title, start_datetime, end_datetime, status FROM Booking 
                       WHERE room_id = %s AND status IN ('confirmed','pending') 
                       AND start_datetime < %s AND end_datetime > %s ORDER BY start_datetime""",
                    (room["room_id"], end_dt, start_dt),
                )
                conflicts = cur.fetchall()
                for c in conflicts: _serialize(c)
                room["is_available"] = len(conflicts) == 0
                room["conflicts"]    = conflicts
                cur.execute("SELECT name, type, status FROM Equipment WHERE room_id=%s AND is_room_fixed=TRUE", (room["room_id"],))
                room["equipment"] = cur.fetchall()
        return {"rooms": rooms, "check_date": check_date, "start_time": start_time, "end_time": end_time}
    finally:
        conn.close()

# API ใหม่สำหรับการอัปเดตข้อมูลห้องประชุม
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
            cur.execute(f"UPDATE Room SET {', '.join(fields)} WHERE room_id=%s", tuple(values))
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
                cur.execute("SELECT * FROM Equipment WHERE is_room_fixed=FALSE ORDER BY type, name")
            else:
                cur.execute("SELECT * FROM Equipment ORDER BY is_room_fixed DESC, type, name")
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
                """INSERT INTO Equipment (room_id, name, type, is_room_fixed, status, description)
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
            cur.execute(f"UPDATE Equipment SET {', '.join(fields)} WHERE equipment_id=%s", tuple(values))
        conn.commit()
        return {"message": "อัปเดตสำเร็จ"}
    finally:
        conn.close()

@app.delete("/api/equipment/{equipment_id}")
def delete_equipment(equipment_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM Booking_Equipment WHERE equipment_id=%s", (equipment_id,))
            cur.execute("DELETE FROM Equipment WHERE equipment_id=%s", (equipment_id,))
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
                     FROM Booking b JOIN USER u ON b.user_id = u.user_id JOIN Room r ON b.room_id = r.room_id WHERE 1=1"""
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
                # ดึงผู้เข้าร่วม
                cur.execute("SELECT * FROM Booking_attendee WHERE booking_id=%s", (bk["booking_id"],))
                bk["attendees"] = cur.fetchall()
                
                # 👇 จุดที่เพิ่มใหม่: ดึงชื่ออุปกรณ์ส่วนกลางที่ถูกจองในคิวนี้ออกมาด้วย 👇
                cur.execute("""
                    SELECT e.equipment_id, e.name, e.type 
                    FROM Booking_Equipment be
                    JOIN Equipment e ON be.equipment_id = e.equipment_id
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

    if end_dt <= start_dt: raise HTTPException(status_code=422, detail="End before start")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT booking_id FROM Booking WHERE room_id = %s AND status IN ('confirmed','pending') AND start_datetime < %s AND end_datetime > %s",
                        (payload.room_id, end_dt, start_dt))
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="ห้องถูกจองแล้วเวลานี้")

            cur.execute("""INSERT INTO Booking (user_id, room_id, title, start_datetime, end_datetime, status, require_break, break_note, note)
                           VALUES (%s,%s,%s,%s,%s,'confirmed',%s,%s,%s)""",
                        (payload.user_id, payload.room_id, payload.title, start_dt, end_dt, payload.require_break, payload.break_note, payload.note))
            booking_id = cur.lastrowid

            for email in payload.attendee_emails:
                if email.strip():
                    cur.execute("INSERT INTO Booking_attendee (booking_id, email, notify_status) VALUES (%s,%s,'pending')", (booking_id, email.strip()))
            for eq_id in payload.equipment_ids:
                cur.execute("INSERT INTO Booking_Equipment (booking_id, equipment_id, quantity) VALUES (%s,%s,1)", (booking_id, eq_id))
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
            cur.execute("UPDATE Booking SET status='cancelled' WHERE booking_id=%s", (booking_id,))
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
            month_start = today.replace(day=1)
            now = datetime.now()
            cur.execute("SELECT COUNT(*) AS cnt FROM Room")
            total_rooms = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) AS cnt FROM Booking WHERE DATE(start_datetime) = %s AND status != 'cancelled'", (today,))
            today_bookings = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(DISTINCT room_id) AS cnt FROM Booking WHERE status IN ('confirmed','pending') AND start_datetime <= %s AND end_datetime >= %s", (now, now))
            available_now = total_rooms - cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) AS cnt FROM Booking WHERE DATE(start_datetime) >= %s AND status != 'cancelled'", (month_start,))
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
                           FROM Room r LEFT JOIN Booking b ON b.room_id = r.room_id AND DATE(b.start_datetime) >= %s AND b.status != 'cancelled'
                           GROUP BY r.room_id ORDER BY r.capacity DESC""", (month_start,))
            rows = cur.fetchall()
            for r in rows:
                used = float(r["hours_used"] or 0)
                r["hours_used"] = used
                r["usage_percent"] = round(min(used / 180 * 100, 100), 1)
        return {"usage": rows}
    finally:
        conn.close()
