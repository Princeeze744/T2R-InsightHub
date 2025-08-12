import streamlit as st
import pandas as pd
import plotly.express as px
from t2r_database import T2RDatabase
from datetime import datetime, timedelta

# Password protection
def check_password():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        
    if not st.session_state.authenticated:
        st.title("Trade2Retire InsightHub Pro")
        password = st.text_input("Enter System Password:", type="password")
        if password == "Trade2Retire2023":  # CHANGE TO YOUR SECURE PASSWORD
            st.session_state.authenticated = True
            st.rerun()
        elif password != "":
            st.error("Incorrect password")
        return False
    return True

if not check_password():
    st.stop()

# Initialize database
db = T2RDatabase()

# Page configuration
st.set_page_config(
    page_title="Trade2Retire InsightHub Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    :root {
        --primary: #1e3a8a;
        --secondary: #0f172a;
        --accent: #38bdf8;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
    }
    
    .main {
        background-color: #f8fafc;
    }
    .report-title {
        color: var(--primary);
        font-size: 2.5rem;
        font-weight: 700;
    }
    .trade-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        border-left: 4px solid var(--accent);
    }
    .stButton>button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white;
        border-radius: 8px;
        padding: 12px 28px;
        font-weight: 600;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%);
        color: white;
    }
    .stSelectbox, .stTextInput, .stNumberInput, .stDateInput {
        border-radius: 8px;
    }
    .stTab {
        border-radius: 12px;
        overflow: hidden;
    }
    .stDataFrame {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="trade-header"><h1 class="report-title">Trade2Retire InsightHub Pro</h1><p>Advanced Analytics for Forex Education Excellence</p></div>', unsafe_allow_html=True)

# Sidebar for data entry
with st.sidebar:
    st.header("➕ Add New Data")
    data_type = st.radio("Select data type:", ("Student", "Marketing Campaign", "Payment", "Student Performance"))
    
    if data_type == "Student":
        with st.form("student_form", clear_on_submit=True):
            st.subheader("New Student Registration")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            program = st.selectbox("Program", ["AI", "Beginner", "Gold", "VIP"])
            payment_status = st.selectbox("Payment Status", ["Paid", "Partial", "Unpaid"])
            amount_paid = st.number_input("Amount Paid ($)", min_value=0.0)
            source = st.selectbox("Source", ["Facebook", "Radio", "YouTube", "Referral", "Instagram", "Google Ads"])
            
            if st.form_submit_button("Add Student"):
                db.add_student(name, email, phone, program, payment_status, amount_paid, source)
                st.success("Student added successfully!")
                st.rerun()
    
    elif data_type == "Marketing Campaign":
        with st.form("campaign_form", clear_on_submit=True):
            st.subheader("New Marketing Campaign")
            platform = st.selectbox("Platform", ["Facebook", "Radio", "YouTube", "Instagram", "Google Ads", "Twitter"])
            campaign_name = st.text_input("Campaign Name")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
            spend = st.number_input("Total Spend ($)", min_value=0.0)
            leads_generated = st.number_input("Leads Generated", min_value=0)
            
            if st.form_submit_button("Add Campaign"):
                db.add_campaign(platform, campaign_name, str(start_date), str(end_date), spend, leads_generated)
                st.success("Campaign added successfully!")
                st.rerun()
    
    elif data_type == "Payment":
        with st.form("payment_form", clear_on_submit=True):
            st.subheader("Record Payment")
            students = db.get_students()
            if not students.empty:
                student_options = {row['id']: f"{row['name']} ({row['program']})" for _, row in students.iterrows()}
                student_id = st.selectbox("Student", options=list(student_options.keys()), 
                                          format_func=lambda x: student_options[x])
                amount = st.number_input("Amount ($)", min_value=0.01)
                method = st.selectbox("Payment Method", ["Bank Transfer", "Credit Card", "PayPal", "Crypto"])
                transaction_id = st.text_input("Transaction ID (Optional)")
                
                if st.form_submit_button("Record Payment"):
                    db.record_payment(student_id, amount, method, transaction_id)
                    st.success("Payment recorded successfully!")
                    st.rerun()
            else:
                st.warning("No students available to record payment")
    
    else:  # Student Performance
        with st.form("performance_form", clear_on_submit=True):
            st.subheader("Update Student Performance")
            students = db.get_students()
            if not students.empty:
                student_options = {row['id']: f"{row['name']} ({row['program']})" for _, row in students.iterrows()}
                student_id = st.selectbox("Student", options=list(student_options.keys()), 
                                          format_func=lambda x: student_options[x])
                
                col1, col2 = st.columns(2)
                with col1:
                    assessment_score = st.slider("Assessment Score (0-100)", 0, 100, 70)
                with col2:
                    risk_score = st.slider("Risk Score (1-10)", 1, 10, 5)
                
                performance_rating = st.slider("Performance Rating (1-5)", 1, 5, 3)
                
                if st.form_submit_button("Update Performance"):
                    db.update_student_performance(student_id, assessment_score, risk_score, performance_rating)
                    st.success("Student performance updated successfully!")
                    st.rerun()
            else:
                st.warning("No students available to update performance")

# Main Dashboard
st.header("📊 Executive Dashboard")

# Real-time metrics
col1, col2, col3, col4 = st.columns(4)
students = db.get_students()
campaigns = db.get_campaigns()

with col1:
    st.metric("Total Students", len(students) if not students.empty else 0)
    
with col2:
    total_revenue = students['amount_paid'].sum() if not students.empty else 0
    st.metric("Total Revenue", f"${total_revenue:,.2f}")

with col3:
    marketing_spend = campaigns['spend'].sum() if not campaigns.empty else 0
    st.metric("Marketing Spend", f"${marketing_spend:,.2f}")

with col4:
    if marketing_spend > 0:
        roi = (total_revenue - marketing_spend) / marketing_spend * 100
    else:
        roi = 0
    st.metric("Marketing ROI", f"{roi:.1f}%", delta_color="inverse" if roi < 0 else "normal")

# Charts and analysis
tab1, tab2, tab3, tab4 = st.tabs(["📈 Marketing Analytics", "🎓 Student Performance", "💰 Financial Reports", "⚙️ System Admin"])

with tab1:
    st.subheader("Marketing Performance Analysis")
    
    if not campaigns.empty:
        # ROI by platform
        roi_df = db.calculate_roi()
        if not roi_df.empty:
            st.write("**ROI by Marketing Source**")
            fig = px.bar(roi_df, x='source', y='roi', 
                         labels={'source': 'Marketing Source', 'roi': 'ROI (%)'},
                         color='roi', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
        
            # Display ROI metrics
            st.write("**Marketing Channel Performance**")
            st.dataframe(roi_df[['source', 'students', 'revenue', 'spend', 'roi']])
        else:
            st.info("Add marketing campaigns and student data to see ROI analysis")
        
        # Spend vs Leads
        st.write("**Campaign Performance**")
        fig = px.scatter(campaigns, x='spend', y='leads_generated', size='leads_generated',
                         color='platform', hover_name='campaign_name',
                         title='Spend vs Leads Generated')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No marketing campaigns added yet")

with tab2:
    st.subheader("Student Performance Analysis")
    
    if not students.empty:
        # Program distribution
        st.write("**Program Enrollment Distribution**")
        program_counts = students['program'].value_counts()
        fig = px.pie(program_counts, names=program_counts.index, values=program_counts.values)
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance metrics - with safeguards
        st.write("**Performance Metrics**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'assessment_score' in students.columns:
                avg_score = students['assessment_score'].mean()
                st.metric("Average Assessment Score", f"{avg_score:.1f}/100")
            else:
                st.warning("Assessment data not available")
                
        with col2:
            if 'risk_score' in students.columns:
                avg_risk = students['risk_score'].mean()
                st.metric("Average Risk Score", f"{avg_risk:.1f}/10")
            else:
                st.warning("Risk data not available")
                
        with col3:
            if 'performance_rating' in students.columns:
                avg_perf = students['performance_rating'].mean()
                st.metric("Average Performance Rating", f"{avg_perf:.1f}/5")
            else:
                st.warning("Performance data not available")
        
        # Top performers - with safeguards
        st.write("**Top Performers**")
        if 'assessment_score' in students.columns and 'performance_rating' in students.columns:
            top_performers = students.sort_values('assessment_score', ascending=False).head(5)
            st.dataframe(top_performers[['name', 'program', 'assessment_score', 'performance_rating']])
        else:
            st.warning("Performance data not available for top performers")
        
        # Success prediction
        st.write("**Student Success Prediction**")
        if st.button("Generate Predictions"):
            predictions = db.predict_student_success()
            if not predictions.empty:
                st.dataframe(predictions.sort_values('success_prediction', ascending=False))
            else:
                st.warning("Not enough data to generate predictions")
    else:
        st.info("No student data available yet")

with tab3:
    st.subheader("Financial Reports")
    
    st.write("**Financial Performance Overview**")
    
    if not students.empty and not campaigns.empty:
        # Display key metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Revenue per Student", f"${total_revenue/len(students):,.2f}" if len(students) > 0 else "$0")
        with col2:
            st.metric("Cost Per Acquisition", f"${marketing_spend/len(students):,.2f}" if len(students) > 0 else "$0")
    
    # Report generation
    st.write("**Generate Financial Report**")
    report_type = st.selectbox("Report Type", ["Monthly", "Quarterly", "Custom"])
    
    if report_type == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())
    
    if st.button("Generate Report"):
        report_file = db.generate_report(report_type.lower())
        st.success("Financial report generated successfully!")
        with open(report_file, "rb") as file:
            st.download_button(
                label="Download PDF Report",
                data=file,
                file_name=report_file,
                mime="application/pdf"
            )

with tab4:
    st.subheader("System Administration")
    
    # Database reset function
    st.write("**Database Management**")
    if st.button("🚨 Reset Entire Database", help="Warning: This will delete all data!"):
        st.warning("Are you sure you want to delete ALL data? This cannot be undone!")
        if st.button("CONFIRM RESET"):
            db.reset_database()
            st.success("Database has been reset. Please restart the application.")
            st.stop()
    
    # Backup and Restore
    st.write("**Backup & Restore**")
    if st.button("Create Database Backup"):
        backup_file = db.backup_database()
        st.success(f"Backup created: {backup_file}")
        with open(backup_file, "rb") as f:
            st.download_button("Download Backup", f.read(), file_name=backup_file)
    
    uploaded_file = st.file_uploader("Upload Backup File", type=["db"])
    if uploaded_file is not None:
        if st.button("Restore Database"):
            # Save uploaded file
            with open("restore.db", "wb") as f:
                f.write(uploaded_file.getvalue())
            # Restore
            db.restore_database("restore.db")
            st.success("Database restored from backup! Refresh to see changes.")
            st.rerun()
    
    # Data export
    st.write("**Data Export**")
    if st.button("Export Student Data to CSV"):
        students = db.get_students()
        st.download_button(
            label="Download Student Data",
            data=students.to_csv(index=False).encode('utf-8'),
            file_name="t2r_students.csv",
            mime="text/csv"
        )
    
    if st.button("Export Marketing Data to CSV"):
        campaigns = db.get_campaigns()
        st.download_button(
            label="Download Marketing Data",
            data=campaigns.to_csv(index=False).encode('utf-8'),
            file_name="t2r_campaigns.csv",
            mime="text/csv"
        )

# Data Tables at the bottom
st.header("📝 Data Management")
tab5, tab6, tab7 = st.tabs(["👨‍🎓 Students", "📢 Marketing Campaigns", "💳 Payments"])

with tab5:
    if not students.empty:
        st.dataframe(students, use_container_width=True, height=400)
        
        # DELETE STUDENT RECORD
        st.subheader("Delete Student Record")
        student_options = {row['id']: f"{row['name']} ({row['program']})" for _, row in students.iterrows()}
        student_to_delete = st.selectbox("Select student to delete", options=list(student_options.keys()), 
                                         format_func=lambda x: student_options[x])
        if st.button("Delete Student"):
            db.delete_student(student_to_delete)
            st.success("Student deleted! Refresh to see changes.")
            st.rerun()
    else:
        st.info("No student data available")

with tab6:
    if not campaigns.empty:
        st.dataframe(campaigns, use_container_width=True, height=400)
        
        # DELETE CAMPAIGN RECORD
        st.subheader("Delete Campaign Record")
        campaign_options = {row['id']: f"{row['campaign_name']} ({row['platform']})" for _, row in campaigns.iterrows()}
        campaign_to_delete = st.selectbox("Select campaign to delete", options=list(campaign_options.keys()), 
                                          format_func=lambda x: campaign_options[x])
        if st.button("Delete Campaign"):
            db.delete_campaign(campaign_to_delete)
            st.success("Campaign deleted! Refresh to see changes.")
            st.rerun()
    else:
        st.info("No marketing campaigns available")

with tab7:
    payments = db.get_payments()
    if not payments.empty:
        st.dataframe(payments, use_container_width=True, height=400)
        
        # DELETE PAYMENT RECORD
        st.subheader("Delete Payment Record")
        payment_to_delete = st.selectbox("Select payment ID to delete", payments['id'])
        if st.button("Delete Payment"):
            db.delete_payment(payment_to_delete)
            st.success("Payment deleted! Refresh to see changes.")
            st.rerun()
    else:
        st.info("No payment records available")

# Footer
st.markdown("---")
st.caption("Trade2Retire InsightHub Pro • Professional Forex Academy Management System")