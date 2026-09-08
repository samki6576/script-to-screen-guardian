import streamlit as st
import pandas as pd
from clickhouse_connect import get_client
import re
import json

# ─── Page Configuration ──────────────────────────────────────
st.set_page_config(
    page_title="Script-to-Screen Guardian",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Script-to-Screen Guardian")
st.caption("Agentic Production Intelligence | Powered by ClickHouse Cloud")

# ─── Connect to ClickHouse ────────────────────────────────────
@st.cache_resource
def connect_clickhouse():
    try:
        client = get_client(
            host="ozi7a3yaeo.asia-southeast1.gcp.clickhouse.cloud",
            port=8443,
            username="default",
            password=".OWvohB3lPC0h",
            database="default",  # ← Using "default" not "production_db"
            secure=True
        )
        
        # Test connection
        result = client.query("SELECT 1")
        if result.first_row[0] == 1:
            return client
        return None
        
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)[:100]}")
        return None

clickhouse = connect_clickhouse()

# ─── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.title("📋 System Status")
    if clickhouse:
        st.success("✅ ClickHouse: Connected")
        st.info("🗄️ Database: default")
        st.info("📡 Host: ozi7a3yaeo.asia-southeast1.gcp.clickhouse.cloud")
    else:
        st.error("❌ ClickHouse: Disconnected")
        st.info("📊 Using demo data")
    
    st.markdown("---")
    st.caption("Built for Agentic Cinema Hackathon")

# ─── Create Tables Function ──────────────────────────────────
def create_tables():
    if not clickhouse:
        return False
    
    try:
        # Create equipment table
        clickhouse.command("""
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
        
        # Create crew table (SINGULAR: crew_schedule, NOT crew_schedules)
        clickhouse.command("""
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
        
        # Insert sample equipment
        clickhouse.command("""
            INSERT INTO equipment_inventory (equipment_name, type, model, status, location, daily_rate)
            SELECT 'ARRI Alexa 35', 'Camera', 'Alexa 35', 'available', 'Studio A', 2500.00
            WHERE NOT EXISTS (SELECT 1 FROM equipment_inventory LIMIT 1)
        """)
        
        clickhouse.command("""
            INSERT INTO equipment_inventory (equipment_name, type, model, status, location, daily_rate)
            SELECT 'Sony Venice', 'Camera', 'Venice 2', 'booked', 'Studio B', 2200.00
            WHERE NOT EXISTS (SELECT 1 FROM equipment_inventory WHERE equipment_name = 'Sony Venice')
        """)
        
        clickhouse.command("""
            INSERT INTO equipment_inventory (equipment_name, type, model, status, location, daily_rate)
            SELECT 'RED Komodo', 'Camera', 'Komodo 6K', 'maintenance', 'Service Center', 1800.00
            WHERE NOT EXISTS (SELECT 1 FROM equipment_inventory WHERE equipment_name = 'RED Komodo')
        """)
        
        # Insert sample crew (SINGULAR: crew_schedule)
        clickhouse.command("""
            INSERT INTO crew_schedule (crew_name, role, available_start, available_end, status)
            SELECT 'John Director', 'Director', '2026-09-10 08:00:00', '2026-09-10 20:00:00', 'confirmed'
            WHERE NOT EXISTS (SELECT 1 FROM crew_schedule LIMIT 1)
        """)
        
        clickhouse.command("""
            INSERT INTO crew_schedule (crew_name, role, available_start, available_end, status)
            SELECT 'Sarah DP', 'Cinematographer', '2026-09-10 08:00:00', '2026-09-10 20:00:00', 'available'
            WHERE NOT EXISTS (SELECT 1 FROM crew_schedule WHERE crew_name = 'Sarah DP')
        """)
        
        clickhouse.command("""
            INSERT INTO crew_schedule (crew_name, role, available_start, available_end, status)
            SELECT 'Mike Sound', 'Sound Engineer', '2026-09-10 09:00:00', '2026-09-10 18:00:00', 'available'
            WHERE NOT EXISTS (SELECT 1 FROM crew_schedule WHERE crew_name = 'Mike Sound')
        """)
        
        clickhouse.command("""
            INSERT INTO crew_schedule (crew_name, role, available_start, available_end, status)
            SELECT 'Tom Grip', 'Grip', '2026-09-10 07:00:00', '2026-09-10 19:00:00', 'on_leave'
            WHERE NOT EXISTS (SELECT 1 FROM crew_schedule WHERE crew_name = 'Tom Grip')
        """)
        
        return True
    except Exception as e:
        st.error(f"Error creating tables: {e}")
        return False

# ─── Check Tables ────────────────────────────────────────────
def tables_exist():
    if not clickhouse:
        return False
    
    try:
        # Check equipment table
        eq_check = clickhouse.query("""
            SELECT count() FROM system.tables 
            WHERE database = 'default' AND name = 'equipment_inventory'
        """)
        
        # Check crew table (SINGULAR)
        crew_check = clickhouse.query("""
            SELECT count() FROM system.tables 
            WHERE database = 'default' AND name = 'crew_schedule'
        """)
        
        return eq_check.first_row[0] > 0 and crew_check.first_row[0] > 0
    except:
        return False

# ─── Main Content ────────────────────────────────────────────

# Check if tables exist, create if not
if clickhouse and not tables_exist():
    st.info("📝 Setting up tables...")
    if create_tables():
        st.success("✅ Tables created with sample data!")
        st.rerun()

# Display data
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
        
        # ── Query Crew (SINGULAR) ──
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
        
        # ── Display Stats ──
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("🎥 Equipment", len(equipment) if not equipment.empty else 0)
        with col2:
            available = len(equipment[equipment['status'] == 'available']) if not equipment.empty else 0
            st.metric("✅ Available", available)
        with col3:
            maintenance = len(equipment[equipment['status'] == 'maintenance']) if not equipment.empty else 0
            st.metric("🔧 Maintenance", maintenance, "⚠️ Risk" if maintenance > 0 else "✅ Clear")
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
                st.dataframe(equipment, use_container_width=True)
                st.bar_chart(equipment['status'].value_counts())
            else:
                st.info("No equipment data")
        
        with col2:
            st.subheader("👥 Crew")
            if not crew.empty:
                st.dataframe(crew, use_container_width=True)
                st.bar_chart(crew['status'].value_counts())
            else:
                st.info("No crew data")
        
        # ── Script Analysis ──
        st.subheader("🎭 Script Analysis")
        
        script = st.text_area(
            "Paste a script scene:",
            height=100,
            placeholder="SCENE 12 - EXT. ABANDONED WAREHOUSE - DAY\n\nJACK and SARAH enter..."
        )
        
        if st.button("🔍 Analyze") and script:
            st.subheader("📋 Analysis")
            
            # Extract location
            loc_match = re.search(r'(?:INT|EXT)\.\s*([^\n]+)', script)
            location = loc_match.group(1).strip() if loc_match else "Unknown"
            
            # Extract characters
            chars = re.findall(r'([A-Z][A-Z\s]+)(?=\n)', script)
            characters = [c.strip() for c in chars[:3]] if chars else ["Unknown"]
            
            # Extract props
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
            
            # Check risks
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
        st.dataframe(demo_equipment, use_container_width=True)
    with col2:
        st.subheader("👥 Crew (Demo)")
        st.dataframe(demo_crew, use_container_width=True)

st.markdown("---")
st.caption("🎬 Script-to-Screen Guardian | Built for Agentic Cinema Hackathon")