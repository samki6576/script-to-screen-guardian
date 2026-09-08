import os

import streamlit as st
import pandas as pd
from clickhouse_connect import get_client
import re
import urllib.parse

# ─── Page Configuration ──────────────────────────────────────
st.set_page_config(
    page_title="Script-to-Screen Guardian",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Script-to-Screen Guardian")
st.caption("Agentic Production Intelligence | Powered by ClickHouse Cloud")

# ─── Connect to ClickHouse ────────────────────────────────────
def _secret_or_env(name: str, default: str = "") -> str:
    value = st.secrets.get(name, os.getenv(name, default))
    return str(value)


def connect_clickhouse():
    try:
        client = get_client(
            host=_secret_or_env("CLICKHOUSE_HOST", "localhost"),
            port=int(_secret_or_env("CLICKHOUSE_PORT", "8123")),
            username=_secret_or_env("CLICKHOUSE_USER", "default"),
            password=_secret_or_env("CLICKHOUSE_PASSWORD"),
            database=_secret_or_env("CLICKHOUSE_DATABASE", "default"),
            secure=_secret_or_env("CLICKHOUSE_SECURE", "false").lower() == "true",
            connect_timeout=30,
            send_receive_timeout=30,
        )

        result = client.query("SELECT 1")
        if result.first_row and result.first_row[0] == 1:
            return client
        client.close()
        return None
    except Exception as e:
        st.error("❌ Connection failed. Check the ClickHouse values in Streamlit Secrets.")
        return None


def can_connect_clickhouse() -> bool:
    client = connect_clickhouse()
    if client is None:
        return False
    try:
        result = client.query("SELECT 1")
        return bool(result.first_row and result.first_row[0] == 1)
    finally:
        client.close()


clickhouse = connect_clickhouse()

# ─── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.title("📋 System Status")
    if clickhouse:
        st.success("✅ ClickHouse: Connected")
        st.info("🗄️ Database: default")
    else:
        st.error("❌ ClickHouse: Disconnected")
        st.info("📊 Using demo data")
    
    st.markdown("---")
    st.caption("Built for Agentic Cinema Hackathon")

# ─── Create Tables Function ──────────────────────────────────
def create_tables():
    client = connect_clickhouse()
    if not client:
        return False

    try:
        client.command("""
            CREATE TABLE IF NOT EXISTS equipment_inventory (
                equipment_id UUID DEFAULT generateUUIDv4(),
                equipment_name String,
                type String,
                model String,
                status String,
                location String,
                daily_rate Decimal(10,2),
                created_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY (equipment_id, created_at)
        """)

        client.command("""
            CREATE TABLE IF NOT EXISTS crew_schedule (
                crew_id UUID DEFAULT generateUUIDv4(),
                crew_name String,
                role String,
                available_start DateTime,
                available_end DateTime,
                status String,
                created_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY (crew_id, available_start)
        """)

        count = client.query("SELECT count() FROM equipment_inventory")
        if count.first_row and count.first_row[0] == 0:
            client.command("""
                INSERT INTO equipment_inventory (equipment_name, type, model, status, location, daily_rate)
                VALUES 
                ('ARRI Alexa 35', 'Camera', 'Alexa 35', 'available', 'Studio A', 2500.00),
                ('Sony Venice', 'Camera', 'Venice 2', 'booked', 'Studio B', 2200.00),
                ('RED Komodo', 'Camera', 'Komodo 6K', 'maintenance', 'Service Center', 1800.00),
                ('Lighting Kit Pro', 'Lighting', 'Aputure 1200D', 'available', 'Studio A', 800.00),
                ('Dolly Track', 'Grip', 'Chapman Hybrid', 'available', 'Warehouse', 500.00)
            """)

        count = client.query("SELECT count() FROM crew_schedule")
        if count.first_row and count.first_row[0] == 0:
            client.command("""
                INSERT INTO crew_schedule (crew_name, role, available_start, available_end, status)
                VALUES 
                ('John Director', 'Director', '2026-09-10 08:00:00', '2026-09-10 20:00:00', 'confirmed'),
                ('Sarah DP', 'Cinematographer', '2026-09-10 08:00:00', '2026-09-10 20:00:00', 'available'),
                ('Mike Sound', 'Sound Engineer', '2026-09-10 09:00:00', '2026-09-10 18:00:00', 'available'),
                ('Tom Grip', 'Grip', '2026-09-10 07:00:00', '2026-09-10 19:00:00', 'on_leave')
            """)

        return True
    except Exception as e:
        st.error(f"Error creating tables: {e}")
        return False
    finally:
        client.close()

# ─── Check Tables ────────────────────────────────────────────
def tables_exist():
    client = connect_clickhouse()
    if not client:
        return False

    try:
        eq_check = client.query("""
            SELECT count() FROM system.tables 
            WHERE database = 'default' AND name = 'equipment_inventory'
        """)

        crew_check = client.query("""
            SELECT count() FROM system.tables 
            WHERE database = 'default' AND name = 'crew_schedule'
        """)

        return bool(eq_check.first_row and crew_check.first_row and eq_check.first_row[0] > 0 and crew_check.first_row[0] > 0)
    except Exception:
        return False
    finally:
        client.close()

# ─── Main Content ────────────────────────────────────────────

# Check if tables exist, create if not
if clickhouse and not tables_exist():
    st.info("📝 Setting up tables...")
    if create_tables():
        st.success("✅ Tables created with sample data!")
        st.rerun()

# Display data from ClickHouse if connected
if clickhouse and tables_exist():
    try:
        # ── Query Equipment ──
        eq_result = clickhouse.query("""
            SELECT equipment_name, type, model, status, location, daily_rate
            FROM equipment_inventory
            ORDER BY equipment_name
        """)
        
        if eq_result.row_count > 0:
            equipment = pd.DataFrame(
                eq_result.result_rows,
                columns=eq_result.column_names
            )
        else:
            equipment = pd.DataFrame()
        
        # ── Query Crew ──
        crew_result = clickhouse.query("""
            SELECT crew_name, role, available_start, available_end, status
            FROM crew_schedule
            ORDER BY crew_name
        """)
        
        if crew_result.row_count > 0:
            crew = pd.DataFrame(
                crew_result.result_rows,
                columns=crew_result.column_names
            )
        else:
            crew = pd.DataFrame()
        
        # ── Stats ──
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("🎥 Equipment", len(equipment) if not equipment.empty else 0)
        with col2:
            available = len(equipment[equipment['status'] == 'available']) if not equipment.empty else 0
            st.metric("✅ Available", available)
        with col3:
            maintenance = len(equipment[equipment['status'] == 'maintenance']) if not equipment.empty else 0
            st.metric("🔧 Maintenance", maintenance, "⚠️ Risk" if maintenance > 0 else None)
        with col4:
            st.metric("👥 Crew", len(crew) if not crew.empty else 0)
        with col5:
            avail_crew = len(crew[crew['status'].isin(['available', 'confirmed'])]) if not crew.empty else 0
            st.metric("🟢 Available", avail_crew)
        
        # ── Risk Alerts ──
        if not equipment.empty:
            risks = equipment[equipment['status'].isin(['maintenance', 'booked'])]
            if not risks.empty:
                st.subheader("⚠️ Risk Alerts")
                for _, row in risks.iterrows():
                    st.warning(f"🚨 **{row['equipment_name']}** - {row['status']} at {row.get('location', 'Unknown')}")
            else:
                st.success("✅ No equipment risks!")
        
        # ── Tables ──
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📦 Equipment")
            if not equipment.empty:
                st.dataframe(equipment, width='stretch')
                st.bar_chart(equipment['status'].value_counts())
            else:
                st.info("No equipment data")
        
        with col2:
            st.subheader("👥 Crew")
            if not crew.empty:
                st.dataframe(crew, width='stretch')
                st.bar_chart(crew['status'].value_counts())
            else:
                st.info("No crew data")
        
        # ── Script Analysis ──
        st.subheader("🎭 Script Analysis")

        uploaded_file = st.file_uploader(
            "Upload a script file:",
            type=["txt", "fdx", "md"],
            help="Upload a plain-text, Fountain, or Final Draft script file.",
        )
        uploaded_script = (
            uploaded_file.getvalue().decode("utf-8", errors="replace")
            if uploaded_file is not None
            else ""
        )
        
        script = st.text_area(
            "Paste a script scene:",
            height=100,
            value=uploaded_script,
            placeholder="SCENE 12 - EXT. ABANDONED WAREHOUSE - DAY\n\nJACK and SARAH enter..."
        )
        
        if st.button("🔍 Analyze") and script:
            st.subheader("📋 Analysis")
            
            loc_match = re.search(r'(?:INT|EXT)\.\s*([^\n]+)', script)
            location = loc_match.group(1).strip() if loc_match else "Unknown"
            
            chars = re.findall(r'([A-Z][A-Z\s]+)(?=\n)', script)
            characters = [c.strip() for c in chars[:3]] if chars else ["Unknown"]
            
            props = []
            if "flashlight" in script.lower():
                props.append("Flashlight")
            if "device" in script.lower():
                props.append("Device")
            if "rain" in script.lower() or "water" in script.lower():
                props.append("Rain effect")
            
            st.write(f"**Location:** {location}")
            st.write(f"**Characters:** {', '.join(characters)}")
            st.write(f"**Props:** {', '.join(props) if props else 'None detected'}")
            
            risks_found = []
            if "rain" in script.lower() or "water" in script.lower():
                risks_found.append("🌧️ Weather effects required - check rain machine")
            if "crash" in script.lower() or "explosion" in script.lower():
                risks_found.append("💥 Special effects - permit needed")
            
            if risks_found:
                st.warning("⚠️ **Risks Identified:**")
                for r in risks_found:
                    st.write(f"• {r}")
            else:
                st.success("✅ No immediate risks")
        
    except Exception as e:
        st.error(f"Error: {e}")
        show_demo = True

else:
    show_demo = True

# ─── Demo Data ──────────────────────────────────────────────
if 'show_demo' in locals() and show_demo:
    st.info("📊 Demo Data (ClickHouse not connected)")
    
    demo_equipment = pd.DataFrame([
        {"equipment_name": "ARRI Alexa 35", "type": "Camera", "status": "available", "location": "Studio A", "daily_rate": 2500.00},
        {"equipment_name": "Sony Venice", "type": "Camera", "status": "booked", "location": "Studio B", "daily_rate": 2200.00},
        {"equipment_name": "RED Komodo", "type": "Camera", "status": "maintenance", "location": "Service Center", "daily_rate": 1800.00},
        {"equipment_name": "Lighting Kit Pro", "type": "Lighting", "status": "available", "location": "Studio A", "daily_rate": 800.00},
        {"equipment_name": "Dolly Track", "type": "Grip", "status": "available", "location": "Warehouse", "daily_rate": 500.00},
    ])
    
    demo_crew = pd.DataFrame([
        {"crew_name": "John Director", "role": "Director", "status": "confirmed"},
        {"crew_name": "Sarah DP", "role": "Cinematographer", "status": "available"},
        {"crew_name": "Mike Sound", "role": "Sound Engineer", "status": "available"},
        {"crew_name": "Tom Grip", "role": "Grip", "status": "on_leave"},
    ])
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 Equipment (Demo)")
        st.dataframe(demo_equipment, width='stretch')
        st.bar_chart(demo_equipment['status'].value_counts())
    with col2:
        st.subheader("👥 Crew (Demo)")
        st.dataframe(demo_crew, width='stretch')
        st.bar_chart(demo_crew['status'].value_counts())

st.markdown("---")
st.caption("🎬 Script-to-Screen Guardian | Built for Agentic Cinema Hackathon")

# ─── Debug Info ──────────────────────────────────────────────
with st.expander("🔧 Debug Info"):
    st.write("**ClickHouse Connection Attempt:**")
    st.write(f"Host: {_secret_or_env('CLICKHOUSE_HOST', 'localhost')}")
    st.write(f"Port: {_secret_or_env('CLICKHOUSE_PORT', '8123')}")
    st.write(f"Username: {_secret_or_env('CLICKHOUSE_USER', 'default')}")
    st.write(f"Database: {_secret_or_env('CLICKHOUSE_DATABASE', 'default')}")
    st.write(f"Connected: {clickhouse is not None}")
    
    if clickhouse:
        try:
            version = clickhouse.query("SELECT version()")
            st.success(f"Version: {version.first_row[0]}")
        except Exception as e:
            st.error(f"Version check failed: {e}")