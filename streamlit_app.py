import streamlit as st
import pandas as pd
import os
from clickhouse_connect import get_client
import google.generativeai as genai
import json
import re
from datetime import datetime, timedelta

# ─── Page Configuration ──────────────────────────────────────
st.set_page_config(
    page_title="Script-to-Screen Guardian",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Script-to-Screen Guardian")
st.caption("Agentic Production Intelligence | Powered by ClickHouse Cloud + Gemini AI")

# ─── Get Secrets ──────────────────────────────────────────────
def get_secret(key, default=None):
    """Get secret from environment or Streamlit secrets"""
    value = os.getenv(key)
    if value:
        return value
    try:
        return st.secrets.get(key, default)
    except:
        return default

# ─── Connect to ClickHouse ────────────────────────────────────
@st.cache_resource
def connect_clickhouse():
    try:
        client = get_client(
            host="ozi7a3yaeo.asia-southeast1.gcp.clickhouse.cloud",
            port=8443,
            username="default",
            password=".OWvohB3lPC0h",
            database="default",  # ← Using default database
            secure=True
        )
        
        # Test connection
        result = client.query("SELECT 1")
        if result.first_row[0] == 1:
            st.success("✅ Connected to ClickHouse Cloud!")
            return client
        else:
            st.error("❌ Connection test failed")
            return None
        
    except Exception as e:
        st.error(f"❌ ClickHouse connection failed: {str(e)[:150]}")
        return None

# ─── Connect to Gemini ────────────────────────────────────────
@st.cache_resource
def setup_gemini():
    try:
        api_key = get_secret('GEMINI_API_KEY')
        if not api_key:
            # Hardcode for testing if you have a key
            api_key = "YOUR_GEMINI_API_KEY_HERE"
        
        if api_key and api_key != "YOUR_GEMINI_API_KEY_HERE":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            return model
        else:
            st.warning("⚠️ Gemini API key not set. Using fallback mode.")
            return None
    except Exception as e:
        st.warning(f"⚠️ Gemini setup failed: {e}")
        return None

# ─── Initialize Connections ───────────────────────────────────
clickhouse = connect_clickhouse()
gemini = setup_gemini()

# ─── Sidebar Status ──────────────────────────────────────────
with st.sidebar:
    st.title("📋 System Status")
    
    if clickhouse:
        st.success("✅ ClickHouse: Connected")
        st.info("🗄️ Database: default")
    else:
        st.error("❌ ClickHouse: Disconnected")
    
    if gemini:
        st.success("✅ Gemini: Configured")
    else:
        st.warning("⚠️ Gemini: Fallback mode")
    
    st.markdown("---")
    st.caption("Built for Agentic Cinema Hackathon")

# ─── Check Tables Exist ──────────────────────────────────────
def check_tables():
    if not clickhouse:
        return False
    
    try:
        # Check equipment table
        eq_check = clickhouse.query("""
            SELECT count() FROM system.tables 
            WHERE database = 'default' AND name = 'equipment_inventory'
        """)
        
        if eq_check.first_row[0] == 0:
            st.warning("⚠️ Table 'equipment_inventory' does not exist. Please create it.")
            return False
        
        # Check crew table
        crew_check = clickhouse.query("""
            SELECT count() FROM system.tables 
            WHERE database = 'default' AND name = 'crew_schedule'
        """)
        
        if crew_check.first_row[0] == 0:
            st.warning("⚠️ Table 'crew_schedule' does not exist. Please create it.")
            return False
        
        return True
    except Exception as e:
        st.error(f"Error checking tables: {e}")
        return False

# ─── Main Dashboard ──────────────────────────────────────────

# Check if tables exist
tables_exist = check_tables()

if clickhouse and tables_exist:
    try:
        # ── Query Equipment ──
        eq_result = clickhouse.query("""
            SELECT 
                equipment_name,
                type,
                model,
                status,
                location,
                daily_rate
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
            st.info("ℹ️ No equipment data. Run INSERT statements.")
        
        # ── Query Crew ──
        crew_result = clickhouse.query("""
            SELECT 
                crew_name,
                role,
                available_start,
                available_end,
                status
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
            st.info("ℹ️ No crew data. Run INSERT statements.")
        
        # ── Display Stats ──
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_eq = len(equipment) if not equipment.empty else 0
            st.metric("🎥 Total Equipment", total_eq)
        
        with col2:
            available_eq = len(equipment[equipment['status'] == 'available']) if not equipment.empty else 0
            st.metric("✅ Available", available_eq)
        
        with col3:
            maintenance_eq = len(equipment[equipment['status'] == 'maintenance']) if not equipment.empty else 0
            st.metric("🔧 Maintenance", maintenance_eq, 
                     delta="⚠️ Risk" if maintenance_eq > 0 else "✅ Clear")
        
        with col4:
            total_crew = len(crew) if not crew.empty else 0
            st.metric("👥 Total Crew", total_crew)
        
        with col5:
            available_crew = len(crew[crew['status'].isin(['available', 'confirmed'])]) if not crew.empty else 0
            st.metric("🟢 Available Crew", available_crew)
        
        # ── Risk Alerts ──
        if not equipment.empty:
            risks = equipment[equipment['status'].isin(['maintenance', 'booked'])]
            if not risks.empty:
                st.subheader("⚠️ Risk Alerts")
                for _, row in risks.iterrows():
                    st.warning(f"🚨 **{row['equipment_name']}** - {row['status']} at {row.get('location', 'Unknown')}")
            else:
                st.success("✅ No equipment risks detected!")
        
        # ── Two Column Layout ──
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📦 Equipment Inventory")
            if not equipment.empty:
                st.dataframe(equipment, use_container_width=True)
                status_counts = equipment['status'].value_counts()
                st.bar_chart(status_counts)
            else:
                st.info("No equipment data")
        
        with col2:
            st.subheader("👥 Crew Schedule")
            if not crew.empty:
                st.dataframe(crew, use_container_width=True)
                status_counts = crew['status'].value_counts()
                st.bar_chart(status_counts)
            else:
                st.info("No crew data")
        
        # ── Gemini Script Analysis (Optional) ──
        st.subheader("🎭 Script Analysis")
        
        sample_script = st.text_area(
            "Paste a script scene to analyze:",
            height=150,
            placeholder="SCENE 12 - EXT. ABANDONED WAREHOUSE - DAY\n\nJACK and SARAH enter..."
        )
        
        if st.button("🔍 Analyze Scene") and sample_script:
            with st.spinner("Analyzing with Gemini..."):
                if gemini:
                    try:
                        prompt = f"""
                        Analyze this film script scene and extract:
                        1. Location
                        2. Characters
                        3. Props needed
                        4. Special effects/requirements
                        5. Potential production risks

                        Script:
                        {sample_script}

                        Return as JSON with keys: location, characters, props, requirements, risks
                        """
                        
                        response = gemini.generate_content(prompt)
                        st.success("✅ Analysis complete!")
                        
                        try:
                            # Try to parse as JSON
                            result = json.loads(response.text)
                            st.json(result)
                        except:
                            # Show raw response
                            st.write(response.text)
                    except Exception as e:
                        st.error(f"Gemini analysis failed: {e}")
                        st.info("Using fallback analysis...")
                        show_fallback_analysis(sample_script)
                else:
                    st.info("Gemini not configured. Using fallback analysis.")
                    show_fallback_analysis(sample_script)
            
    except Exception as e:
        st.error(f"Error: {e}")
        show_demo = True

else:
    show_demo = True

# ─── Fallback Analysis ──────────────────────────────────────
def show_fallback_analysis(script):
    """Show fallback analysis when Gemini is unavailable"""
    st.subheader("📋 Fallback Analysis")
    
    # Simple extraction
    location_match = re.search(r'(?:INT|EXT)\.\s*([^\n]+)', script)
    location = location_match.group(1).strip() if location_match else "Unknown"
    
    char_match = re.findall(r'([A-Z][A-Z\s]+)(?=\n)', script)
    characters = [c.strip() for c in char_match[:3]] if char_match else ["Unknown"]
    
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
    
    # Check for risks
    risks = []
    if "rain" in script.lower() or "water" in script.lower():
        risks.append("🌧️ Weather effects required - check rain machine availability")
    if "crash" in script.lower() or "explosion" in script.lower():
        risks.append("💥 Special effects required - permit needed")
    
    if risks:
        st.warning("⚠️ **Potential Risks Identified:**")
        for risk in risks:
            st.write(f"• {risk}")
    else:
        st.success("✅ No immediate risks detected")

# ─── Demo Data Fallback ──────────────────────────────────────
if 'show_demo' in locals() and show_demo:
    st.info("📊 Showing demo data")
    
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
        st.dataframe(demo_equipment, use_container_width=True)
        
        # Demo chart
        status_counts = demo_equipment['status'].value_counts()
        st.bar_chart(status_counts)
    
    with col2:
        st.subheader("👥 Crew (Demo)")
        st.dataframe(demo_crew, use_container_width=True)
        
        # Demo chart
        status_counts = demo_crew['status'].value_counts()
        st.bar_chart(status_counts)

# ─── Footer ──────────────────────────────────────────────────
st.markdown("---")
st.caption("🎬 Script-to-Screen Guardian | Built for Agentic Cinema Hackathon")
st.caption(f"📡 ClickHouse: ozi7a3yaeo.asia-southeast1.gcp.clickhouse.cloud")

# ─── Create Tables Button ────────────────────────────────────
if clickhouse and not tables_exist:
    st.info("📝 Tables not found. Click below to create them.")
    
    if st.button("🛠️ Create Tables"):
        try:
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
            
            clickhouse.command("""
                INSERT INTO equipment_inventory (equipment_name, type, model, status, location, daily_rate)
                VALUES 
                ('ARRI Alexa 35', 'Camera', 'Alexa 35', 'available', 'Studio A', 2500.00),
                ('Sony Venice', 'Camera', 'Venice 2', 'booked', 'Studio B', 2200.00),
                ('RED Komodo', 'Camera', 'Komodo 6K', 'maintenance', 'Service Center', 1800.00),
                ('Lighting Kit Pro', 'Lighting', 'Aputure 1200D', 'available', 'Studio A', 800.00),
                ('Dolly Track', 'Grip', 'Chapman Hybrid', 'available', 'Warehouse', 500.00)
            """)
            
            clickhouse.command("""
                INSERT INTO crew_schedule (crew_name, role, available_start, available_end, status)
                VALUES 
                ('John Director', 'Director', '2026-09-10 08:00:00', '2026-09-10 20:00:00', 'confirmed'),
                ('Sarah DP', 'Cinematographer', '2026-09-10 08:00:00', '2026-09-10 20:00:00', 'available'),
                ('Mike Sound', 'Sound Engineer', '2026-09-10 09:00:00', '2026-09-10 18:00:00', 'available'),
                ('Tom Grip', 'Grip', '2026-09-10 07:00:00', '2026-09-10 19:00:00', 'on_leave')
            """)
            
            st.success("✅ Tables created and data inserted! Refresh the page.")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error creating tables: {e}")