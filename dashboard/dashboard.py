import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="SafariCycleQ Admin Dashboard",
    page_icon="🚴‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #ddd;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and process the Firebase JSON data"""
    try:
        # Try to read from the uploaded file first
        with open('data/safari-cycleq-default-rtdb-export.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("❌ Data file not found. Please ensure 'safari-cycleq-default-rtdb-export.json' is in the 'data' folder.")
        return None

def process_rides_data(rides_data):
    """Convert rides data to DataFrame"""
    rides_list = []
    for ride_id, ride_info in rides_data.items():
        ride_info['rideId'] = ride_id
        # Convert timestamps to datetime
        if 'startTime' in ride_info:
            ride_info['startTime'] = pd.to_datetime(ride_info['startTime'])
        if 'endTime' in ride_info:
            ride_info['endTime'] = pd.to_datetime(ride_info['endTime'])
        rides_list.append(ride_info)
    return pd.DataFrame(rides_list)

def process_users_data(users_data):
    """Convert users data to DataFrame"""
    users_list = []
    for user_id, user_info in users_data.items():
        user_info['userId'] = user_id
        user_info['createdAt'] = pd.to_datetime(user_info['createdAt'], unit='ms')
        # Extract wallet balance if available
        if 'wallet' in user_info:
            user_info['wallet_balance'] = user_info['wallet'].get('balance', 0)
        else:
            user_info['wallet_balance'] = 0
        users_list.append(user_info)
    return pd.DataFrame(users_list)

def process_emergency_data(emergency_data):
    """Convert emergency data to DataFrame"""
    emergency_list = []
    for emergency_id, emergency_info in emergency_data.items():
        emergency_info['emergencyId'] = emergency_id
        if 'timestamp' in emergency_info:
            emergency_info['timestamp'] = pd.to_datetime(emergency_info['timestamp'])
        emergency_list.append(emergency_info)
    return pd.DataFrame(emergency_list)

def main():
    # Header
    st.markdown("<h1 class='main-header'>🚴‍♂️ Lungani's CycleQ Dashboard</h1>", unsafe_allow_html=True)
    
    # Load data
    data = load_data()
    if data is None:
        st.stop()
    
    # Sidebar for navigation
    st.sidebar.title("📊 Dashboard Navigation")
    page = st.sidebar.selectbox(
        "Choose a section:",
        ["🏠 Overview", "🚴‍♂️ Rides Analytics", "👥 Users & Memberships", "🚨 Emergency Alerts", "💰 Financial Insights"]
    )
    
    # Process data
    rides_df = process_rides_data(data.get('rides', {}))
    users_df = process_users_data(data.get('users', {}))
    
    if page == "🏠 Overview":
        show_overview(data, rides_df, users_df)
    elif page == "🚴‍♂️ Rides Analytics":
        show_rides_analytics(rides_df)
    elif page == "👥 Users & Memberships":
        show_users_analytics(users_df, data)
    elif page == "🚨 Emergency Alerts":
        show_emergency_analytics(data)
    elif page == "💰 Financial Insights":
        show_financial_analytics(rides_df, users_df, data)

def show_overview(data, rides_df, users_df):
    st.header("📈 System Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_rides = len(rides_df)
        st.metric("🚴‍♂️ Total Rides", f"{total_rides:,}")
    
    with col2:
        total_users = len(users_df)
        st.metric("👥 Total Users", f"{total_users:,}")
    
    with col3:
        total_bikes = len(data.get('bikes', {}))
        st.metric("🚲 Total Bikes", f"{total_bikes:,}")
    
    with col4:
        total_revenue = rides_df['cost'].sum() if not rides_df.empty else 0
        st.metric("💰 Total Revenue", f"E{total_revenue:.2f}")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if not rides_df.empty:
            # Daily rides chart
            rides_df['date'] = rides_df['startTime'].dt.date
            daily_rides = rides_df.groupby('date').size().reset_index(name='rides')
            
            fig = px.line(daily_rides, x='date', y='rides', 
                         title="📊 Daily Rides Trend",
                         labels={'date': 'Date', 'rides': 'Number of Rides'})
            fig.update_traces(line_color='#1f77b4', line_width=3)
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not rides_df.empty:
            # Ride status distribution
            status_counts = rides_df['status'].value_counts()
            
            fig = px.pie(values=status_counts.values, names=status_counts.index,
                        title="🎯 Ride Status Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

def show_rides_analytics(rides_df):
    st.header("🚴‍♂️ Rides Analytics")
    
    if rides_df.empty:
        st.warning("No rides data available.")
        return
    
    # Ride metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_duration = rides_df['duration'].mean() / 60  # Convert to minutes
        st.metric("⏱️ Avg Duration", f"{avg_duration:.1f} min")
    
    with col2:
        avg_distance = rides_df['distance'].mean()
        st.metric("📏 Avg Distance", f"{avg_distance:.1f} km")
    
    with col3:
        avg_cost = rides_df['cost'].mean()
        st.metric("💵 Avg Cost", f"E{avg_cost:.2f}")
    
    with col4:
        completion_rate = (rides_df['status'] == 'completed').mean() * 100
        st.metric("✅ Completion Rate", f"{completion_rate:.1f}%")
    
    st.markdown("---")
    
    # Detailed charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Duration distribution
        fig = px.histogram(rides_df, x='duration', nbins=20,
                          title="⏱️ Ride Duration Distribution",
                          labels={'duration': 'Duration (seconds)', 'count': 'Number of Rides'})
        fig.update_traces(marker_color='skyblue', marker_line_color='navy', marker_line_width=1)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Cost vs Duration
        fig = px.scatter(rides_df, x='duration', y='cost',
                        title="💰 Cost vs Duration Analysis",
                        labels={'duration': 'Duration (seconds)', 'cost': 'Cost (R)'})
        fig.update_traces(marker_color='coral', marker_size=8)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent rides table
    st.subheader("📋 Recent Rides")
    recent_rides = rides_df.nlargest(10, 'startTime')[['rideId', 'bikeId', 'startTime', 'endTime', 'duration', 'distance', 'cost', 'status']]
    st.dataframe(recent_rides, use_container_width=True)

def show_users_analytics(users_df, data):
    st.header("👥 Users & Memberships")
    
    if users_df.empty:
        st.warning("No users data available.")
        return
    
    # User metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = len(users_df)
        st.metric("👥 Total Users", f"{total_users:,}")
    
    with col2:
        avg_wallet = users_df['wallet_balance'].mean()
        st.metric("💰 Avg Wallet Balance", f"E{avg_wallet:.2f}")
    
    with col3:
        total_memberships = len(data.get('memberships', {}))
        st.metric("🎫 Active Memberships", f"{total_memberships:,}")
    
    with col4:
        # Calculate user growth rate
        if len(users_df) > 1:
            users_df_sorted = users_df.sort_values('createdAt')
            recent_users = users_df_sorted.tail(7)
            growth_rate = len(recent_users) / 7 * 30  # Monthly projection
            st.metric("📈 Monthly Growth", f"{growth_rate:.0f} users")
        else:
            st.metric("📈 Monthly Growth", "N/A")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # User registration timeline
        users_df['registration_date'] = users_df['createdAt'].dt.date
        user_registrations = users_df.groupby('registration_date').size().reset_index(name='new_users')
        
        fig = px.bar(user_registrations, x='registration_date', y='new_users',
                    title="📅 User Registrations Over Time",
                    labels={'registration_date': 'Date', 'new_users': 'New Users'})
        fig.update_traces(marker_color='lightgreen')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Wallet balance distribution
        fig = px.histogram(users_df, x='wallet_balance', nbins=15,
                          title="💰 Wallet Balance Distribution",
                          labels={'wallet_balance': 'Wallet Balance (E)', 'count': 'Number of Users'})
        fig.update_traces(marker_color='gold', marker_line_color='orange', marker_line_width=1)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    # Users table
    st.subheader("📋 User Details")
    user_display = users_df[['fullName', 'email', 'phone', 'createdAt', 'wallet_balance']].copy()
    user_display['createdAt'] = user_display['createdAt'].dt.strftime('%Y-%m-%d')
    st.dataframe(user_display, use_container_width=True)

def show_emergency_analytics(data):
    st.header("🚨 Emergency Alerts")
    
    emergencies = data.get('emergencies', {})
    bike_emergencies = []
    
    # Process bike emergency events
    bikes = data.get('bikes', {})
    for bike_id, bike_data in bikes.items():
        emergency_events = bike_data.get('emergency_events', {})
        for event_id, event_data in emergency_events.items():
            if 'emergency' in event_data and event_data['emergency']:
                event_data['bike_id'] = bike_id
                event_data['event_id'] = event_id
                bike_emergencies.append(event_data)
    
    # Emergency metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_emergencies = len(emergencies) + len(bike_emergencies)
        st.metric("🚨 Total Emergencies", f"{total_emergencies:,}")
    
    with col2:
        user_emergencies = len(emergencies)
        st.metric("👤 User Emergencies", f"{user_emergencies:,}")
    
    with col3:
        bike_emergency_count = len(bike_emergencies)
        st.metric("🚲 Bike Emergencies", f"{bike_emergency_count:,}")
    
    with col4:
        # Calculate response time (placeholder)
        st.metric("⏱️ Avg Response Time", "< 5 min")
    
    st.markdown("---")
    
    if emergencies:
        st.subheader("👤 User Emergency Reports")
        emergency_list = []
        for emergency_id, emergency_data in emergencies.items():
            emergency_data['emergencyId'] = emergency_id
            emergency_list.append(emergency_data)
        
        emergency_df = pd.DataFrame(emergency_list)
        st.dataframe(emergency_df, use_container_width=True)
    
    if bike_emergencies:
        st.subheader("🚲 Bike Emergency Events")
        bike_emergency_df = pd.DataFrame(bike_emergencies)
        
        # Map of emergency locations
        if 'lat' in bike_emergency_df.columns and 'lng' in bike_emergency_df.columns:
            st.subheader("📍 Emergency Locations Map")
            map_data = bike_emergency_df[['lat', 'lng']].rename(columns={'lat': 'latitude', 'lng': 'longitude'})
            st.map(map_data)
        
        st.dataframe(bike_emergency_df, use_container_width=True)

def show_financial_analytics(rides_df, users_df, data):
    st.header("💰 Financial Insights")
    
    if rides_df.empty:
        st.warning("No financial data available.")
        return
    
    # Financial metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_revenue = rides_df['cost'].sum()
        st.metric("💰 Total Revenue", f"E{total_revenue:.2f}")
    
    with col2:
        total_wallet_balance = users_df['wallet_balance'].sum()
        st.metric("💳 Total Wallet Balance", f"E{total_wallet_balance:.2f}")
    
    with col3:
        avg_ride_revenue = rides_df['cost'].mean()
        st.metric("📊 Avg Ride Revenue", f"E{avg_ride_revenue:.2f}")
    
    with col4:
        # Calculate monthly recurring revenue from memberships
        memberships = data.get('memberships', {})
        monthly_revenue = sum(membership.get('fee', 0) for membership in memberships.values())
        st.metric("🔄 Monthly Subscription Revenue", f"R{monthly_revenue:.2f}")
    
    st.markdown("---")
    
    # Financial charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue over time
        if not rides_df.empty:
            rides_df['date'] = rides_df['startTime'].dt.date
            daily_revenue = rides_df.groupby('date')['cost'].sum().reset_index()
            
            fig = px.bar(daily_revenue, x='date', y='cost',
                        title="📈 Daily Revenue",
                        labels={'date': 'Date', 'cost': 'Revenue (E)'})
            fig.update_traces(marker_color='green')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Payment status distribution
        if 'paymentStatus' in rides_df.columns:
            payment_status = rides_df['paymentStatus'].value_counts()
            
            fig = px.pie(values=payment_status.values, names=payment_status.index,
                        title="💳 Payment Status Distribution",
                        color_discrete_sequence=px.colors.qualitative.Prism)
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    # Financial summary table
    st.subheader("📊 Revenue Summary")
    revenue_summary = rides_df.groupby('bikeId').agg({
        'cost': ['sum', 'mean', 'count']
    }).round(2)
    revenue_summary.columns = ['Total Revenue', 'Avg Revenue', 'Total Rides']
    st.dataframe(revenue_summary, use_container_width=True)

if __name__ == "__main__":
    main()
