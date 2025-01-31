import streamlit as st
import pandas as pd
import time
from datetime import datetime
import random
import re
from pathlib import Path
import numpy as np
import os

st.set_page_config(
    page_title=" Automated Sales CRM",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .agent-card {
        padding: 20px;
        border-radius: 5px;
        border: 1px solid #f0f0f0;
        margin: 10px 0;
    }
    .log-entry {
        padding: 5px;
        margin: 2px 0;
        border-radius: 3px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

if 'table_container' not in st.session_state:
    st.session_state.table_container = None
if 'leads_df' not in st.session_state:
    st.session_state.leads_df = None
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = False
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []
if 'show_process_button' not in st.session_state:
    st.session_state.show_process_button = False
if 'current_file' not in st.session_state:
    st.session_state.current_file = None

class ActivityLogger:
    def __init__(self):
        self.logs = {
            'supervisor': [],
            'agent_a': [],
            'agent_b': [],
            'system': []
        }
    
    def add_log(self, agent_type, message, status='info'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.logs[agent_type].append({
            'timestamp': timestamp,
            'message': message,
            'status': status
        })

    def get_agent_logs(self, agent_type):
        return self.logs[agent_type]

    def get_all_logs(self):
        all_logs = []
        for agent_type in self.logs:
            all_logs.extend([(agent_type, log) for log in self.logs[agent_type]])
        return sorted(all_logs, key=lambda x: x[1]['timestamp'], reverse=True)

    def clear_logs(self):
        self.logs = {
            'supervisor': [],
            'agent_a': [],
            'agent_b': [],
            'system': []
        }


def generate_sample_data():
    """Generate sample leads data with some invalid emails"""
   
    companies = [
        ('Tech Solutions Inc', 'Technology'),
        ('HealthCare Plus', 'Healthcare'),
        ('Manufacturing Pro', 'Manufacturing'),
        ('Finance Corp', 'Finance'),
        ('Retail Giants', 'Retail'),
        ('Education First', 'Education'),
        ('Green Energy Co', 'Energy'),
        ('Food Services Ltd', 'Food Service'),
        ('Marketing Masters', 'Marketing'),
        ('Construction Hub', 'Construction')
    ]
    
    leads_data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def generate_invalid_email():
        """Generate different types of invalid emails"""
        invalid_formats = [
            f"invalid.email",  
            f"no@marks@here.com",  
            f"spaces in@email.com",  
            f"@nodomain.com", 
            f".invalid@email.com", 
            f"missing_dot@domaincom", 
            f"special#chars@email.com", 
            "" 
        ]
        return random.choice(invalid_formats)
    
    for i in range(5):
        progress = (i + 1) / 5
        progress_bar.progress(progress)
        
        company, industry = random.choice(companies)
        first_name = random.choice(['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'Alex', 'Lisa'])
        last_name = random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis'])
        
        use_invalid_email = random.random() < 0.4
        
        if use_invalid_email:
            email = generate_invalid_email()
        else:
            email = f"{first_name.lower()}.{last_name.lower()}@{company.lower().replace(' ', '')}.com"
        
        lead = {
            'Lead Name': f"{first_name} {last_name}",
            'Email': email,
            'Contact Number': f"+1-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
            'Company': company,
            'Industry': industry,
            'Email Verified': '',
            'Response Status': '',
            'Notes': '',
            'Priority': random.choice(['High', 'Medium', 'Low']),
            'Last Contact': '',
            'Created Date': pd.Timestamp.now().strftime('%Y-%m-%d'),
            'Lead Score': random.randint(1, 100)
        }
        leads_data.append(lead)
        
        email_status = " " if use_invalid_email else ""
        status_text.write(f"Generated lead {i+1}/5: {lead['Lead Name']} from {lead['Company']}{email_status}")
        time.sleep(0.5)

    df = pd.DataFrame(leads_data)
    filename = f"sales_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(filename, index=False)
    
    progress_bar.empty()
    status_text.empty()
    
    return filename, df


class SupervisorAgent:
    def __init__(self, df):
        self.df = df
        
    def monitor_leads(self):
        
        unverified = self.df[
            (self.df['Email Verified'].isna()) | 
            (self.df['Email Verified'] == '')
        ].index
        
        unprocessed = self.df[
            (self.df['Email Verified'] == 'Y') & 
            ((self.df['Response Status'].isna()) | 
             (self.df['Response Status'] == ''))
        ].index
        
        return unverified, unprocessed
    
    def assign_tasks(self):
        unverified, unprocessed = self.monitor_leads()
        return {
            'verification_tasks': unverified.tolist(),
            'outreach_tasks': unprocessed.tolist()
        }
    
    def generate_summary(self):
        total_leads = len(self.df)
        verified_leads = len(self.df[self.df['Email Verified'] == 'Y'])
        responses = self.df['Response Status'].value_counts()
        interested = responses.get('Interested', 0)
        not_interested = responses.get('Not Interested', 0)
        no_response = responses.get('No Response', 0)
        
        avg_lead_score = self.df['Lead Score'].mean()
        high_priority_leads = len(self.df[self.df['Priority'] == 'High'])
        
        return {
            'total_leads': total_leads,
            'verified_leads': verified_leads,
            'interested': interested,
            'not_interested': not_interested,
            'no_response': no_response,
            'verification_rate': f"{(verified_leads/total_leads*100):.1f}%" if total_leads > 0 else "0%",
            'success_rate': f"{(interested/total_leads*100):.1f}%" if total_leads > 0 else "0%",
            'avg_lead_score': f"{avg_lead_score:.1f}",
            'high_priority_leads': high_priority_leads
        }
class AgentA:
    @staticmethod
    def verify_email(email):
        """Simulate email verification with realistic checks"""
        time.sleep(1)  
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False
        return random.choice([True, True, True, False]) 
class AgentB:
    @staticmethod
    def send_campaign_email(lead_info):
        """Simulate sending campaign email"""
        time.sleep(1)  
        response_weights = [0.2, 0.3, 0.5]  
        return np.random.choice(
            ['Interested', 'Not Interested', 'No Response'],
            p=response_weights
        )
def display_agent_activities():
    """Display organized view of agent activities"""
    st.markdown("### 👥 Agent Activities Dashboard")
    
    supervisor_col, agent_a_col, agent_b_col = st.columns(3)
    
    with supervisor_col:
        st.markdown("#### 🎯 Supervisor Agent")
        with st.container():
            st.markdown("**Current Tasks:**")
            if st.session_state.leads_df is not None:
                df = st.session_state.leads_df
                unverified = len(df[df['Email Verified'].isna() | (df['Email Verified'] == '')])
                unprocessed = len(df[
                    (df['Email Verified'] == 'Y') & 
                    (df['Response Status'].isna() | (df['Response Status'] == ''))
                ])
                
                st.info(f"📋 Pending Verifications: {unverified}")
                st.info(f"📨 Pending Outreach: {unprocessed}")
                
                st.markdown("**Priority Distribution:**")
                priority_dist = df['Priority'].value_counts()
                st.progress(float(priority_dist.get('High', 0)) / len(df))
                st.caption(f"High Priority: {priority_dist.get('High', 0)} leads")
    
    with agent_a_col:
        st.markdown("#### ✉️ Agent A (Email Verification)")
        with st.container():
            st.markdown("**Verification Stats:**")
            if st.session_state.leads_df is not None:
                df = st.session_state.leads_df
                verified = len(df[df['Email Verified'] == 'Y'])
                failed = len(df[df['Email Verified'] == 'N'])
                pending = len(df[df['Email Verified'].isna() | (df['Email Verified'] == '')])
                
                st.success(f"✅ Verified: {verified}")
                st.error(f"❌ Failed: {failed}")
                st.info(f"⏳ Pending: {pending}")
                
                if verified + failed > 0:
                    success_rate = verified / (verified + failed) * 100
                    st.progress(success_rate / 100)
                    st.caption(f"Success Rate: {success_rate:.1f}%")
    
    with agent_b_col:
        st.markdown("#### 📧 Agent B (Campaign Outreach)")
        with st.container():
            st.markdown("**Response Stats:**")
            if st.session_state.leads_df is not None:
                df = st.session_state.leads_df
                responses = df['Response Status'].value_counts()
                
                st.success(f"👍 Interested: {responses.get('Interested', 0)}")
                st.error(f"👎 Not Interested: {responses.get('Not Interested', 0)}")
                st.info(f"⏳ No Response: {responses.get('No Response', 0)}")
                
                total_responses = sum(responses)
                if total_responses > 0:
                    interest_rate = (responses.get('Interested', 0) / total_responses) * 100
                    st.progress(interest_rate / 100)
                    st.caption(f"Interest Rate: {interest_rate:.1f}%")

def display_activity_log():
    """Display organized activity log"""
    st.markdown("### 📋 Activity Log")
    
    all_tab, supervisor_tab, agent_a_tab, agent_b_tab = st.tabs([
        "All Activities", "Supervisor Logs", "Agent A Logs", "Agent B Logs"
    ])
    
    log_styles = {
        'supervisor': "🎯",
        'agent_a': "✉️",
        'agent_b': "📧",
        'system': "🔧"
    }
    
    with all_tab:
        all_logs = st.session_state.activity_logger.get_all_logs()
        for agent_type, log in all_logs:
            icon = log_styles.get(agent_type, "")
            status_color = {
                'success': 'green',
                'error': 'red',
                'info': 'blue'
            }.get(log['status'], 'black')
            
            st.markdown(
                f"<div class='log-entry' style='border-left: 3px solid {status_color};'>"
                f"<span style='color: gray'>[{log['timestamp']}]</span> "
                f"{icon} <span style='color: {status_color}'>{log['message']}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
    
    with supervisor_tab:
        for log in st.session_state.activity_logger.get_agent_logs('supervisor'):
            st.markdown(
                f"<div class='log-entry'>[{log['timestamp']}] 🎯 {log['message']}</div>",
                unsafe_allow_html=True
            )
    
    with agent_a_tab:
        for log in st.session_state.activity_logger.get_agent_logs('agent_a'):
            st.markdown(
                f"<div class='log-entry'>[{log['timestamp']}] ✉️ {log['message']}</div>",
                unsafe_allow_html=True
            )
    
    with agent_b_tab:
        for log in st.session_state.activity_logger.get_agent_logs('agent_b'):
            st.markdown(
                f"<div class='log-entry'>[{log['timestamp']}] 📧 {log['message']}</div>",
                unsafe_allow_html=True
            )


def run_automated_workflow():
    """Run the automated workflow with visual feedback"""
    if st.session_state.leads_df is None:
        st.error("No leads data available!")
        return

    supervisor = SupervisorAgent(st.session_state.leads_df)
    logger = st.session_state.activity_logger
    
    logger.clear_logs()
    logger.add_log('system', f"Processing file: {st.session_state.current_file}", 'info')
    
    
    progress_placeholder = st.empty()
    table_placeholder = st.empty()
    activities_container = st.container()
    log_container = st.container()
    
    
    with table_placeholder:
        st.markdown("### Data Preview")
        st.dataframe(st.session_state.leads_df, height=200)
    
    initial_tasks = supervisor.assign_tasks()
    verification_tasks = initial_tasks['verification_tasks']
    
    if len(verification_tasks) == 0 and len(initial_tasks['outreach_tasks']) == 0:
        logger.add_log('supervisor', "No tasks to process", 'info')
        with activities_container:
            display_agent_activities()
        with log_container:
            display_activity_log()
        return
    
    logger.add_log('supervisor', f"Starting email verification for {len(verification_tasks)} leads", 'info')
    completed_tasks = 0
    total_verification_tasks = len(verification_tasks)
    
   
    for idx in verification_tasks:
        lead = st.session_state.leads_df.loc[idx]
        logger.add_log('agent_a', f"Verifying email for {lead['Lead Name']}", 'info')
        
        is_valid = AgentA.verify_email(lead['Email'])
        st.session_state.leads_df.at[idx, 'Email Verified'] = 'Y' if is_valid else 'N'
        
      
        with table_placeholder:
            st.markdown("### Data Preview")
            st.dataframe(st.session_state.leads_df, height=200)
        
        completed_tasks += 1
        progress = min(completed_tasks / (total_verification_tasks * 2), 0.5)
        progress_placeholder.progress(progress)
        
        status = 'success' if is_valid else 'error'
        logger.add_log('agent_a', 
                      f"Email verification {'successful' if is_valid else 'failed'} for {lead['Lead Name']}", 
                      status)
        
        with activities_container:
            display_agent_activities()
        with log_container:
            display_activity_log()
        
        time.sleep(1)
    
    
    updated_tasks = supervisor.assign_tasks()
    outreach_tasks = updated_tasks['outreach_tasks']
    
    if outreach_tasks:
        logger.add_log('supervisor', f"Starting email campaign for {len(outreach_tasks)} verified leads", 'info')
        outreach_completed = 0
        total_outreach = len(outreach_tasks)
        
        for idx in outreach_tasks:
            lead = st.session_state.leads_df.loc[idx]
            logger.add_log('agent_b', f"Sending campaign email to {lead['Lead Name']}", 'info')
            
            response = AgentB.send_campaign_email(lead)
            st.session_state.leads_df.at[idx, 'Response Status'] = response
            st.session_state.leads_df.at[idx, 'Last Contact'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            
            with table_placeholder:
                st.markdown("### Data Preview")
                st.dataframe(st.session_state.leads_df, height=200)
            
            outreach_completed += 1
            progress = 0.5 + (outreach_completed / total_outreach * 0.5)
            progress_placeholder.progress(progress)
            
            status = 'success' if response == 'Interested' else 'info'
            logger.add_log('agent_b', 
                          f"Campaign email sent to {lead['Lead Name']} - Response: {response}", 
                          status)
            
            with activities_container:
                display_agent_activities()
            with log_container:
                display_activity_log()
            
            time.sleep(1)
    
    progress_placeholder.progress(1.0)
    
    
    summary = supervisor.generate_summary()
    st.success("✅ Processing completed!")
    
    st.markdown("### 📊 Campaign Results")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Leads Processed", summary['total_leads'])
        st.metric("Verification Rate", summary['verification_rate'])
    with col2:
        st.metric("Interested Leads", summary['interested'])
        st.metric("Success Rate", summary['success_rate'])
    with col3:
        st.metric("Average Lead Score", summary['avg_lead_score'])
        st.metric("High Priority Leads", summary['high_priority_leads'])
    
    output_filename = f"processed_{st.session_state.current_file}"
    st.session_state.leads_df.to_excel(output_filename, index=False)
    logger.add_log('system', f"Updated leads file saved as '{output_filename}'", 'success')
    
    with open(output_filename, "rb") as file:
        st.download_button(
            label=" Download Updated Leads File ",
            data=file,
            file_name=output_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )




def main():
    st.title(" Automated Sales Campaign CRM")
    
   
    if 'activity_logger' not in st.session_state:
        st.session_state.activity_logger = ActivityLogger()
    
    
    with st.expander("ℹ️ System Guide", expanded=True):
        st.markdown("""
        ##### How to Use This System
        1. Click on **Generate Sample Data** for test data
           
        2. Click on **Start Processing**  to begin automation 
                    
        3. Scroll down **Download Updated Leads File** after processing
        
        4. See All Activities Supervisor Logs Agent A Logs Agent B Logs
        
        """)
    
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📁 Data Management")

        if st.button(" Generate Sample Leads Data "):
            try:
                filename, df = generate_sample_data()
                st.session_state.leads_df = df
                st.session_state.current_file = filename
                st.session_state.show_process_button = True
                st.session_state.activity_logger.clear_logs()
                st.session_state.activity_logger.add_log('system', f"Sample leads data generated and saved as {filename}", 'success')
                
               
                st.session_state.table_container = st.empty()
                with st.session_state.table_container:
                    st.markdown("###  Data Preview")
                    st.dataframe(df, height=200)
                        
            except Exception as e:
                st.error(f"Error generating sample data: {str(e)}")
        
        
        if st.session_state.show_process_button:
            if st.button(" ▶️  Start Processing "):
                run_automated_workflow()
    
    with col2:
        st.markdown("## Upload Your Own Data")
        uploaded_file = st.file_uploader("Upload XLSX file", type=['xlsx'])
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.session_state.leads_df = df
                st.session_state.current_file = uploaded_file.name
                st.session_state.activity_logger.clear_logs()
                st.session_state.activity_logger.add_log('system', "Custom file uploaded successfully", 'success')
                
                
                st.markdown("### Data Preview")
                st.dataframe(df, height=200)
                
               
                if st.button("▶️ Process Uploaded Data"):
                    run_automated_workflow()
                    
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

    
    if st.session_state.leads_df is not None:
        display_agent_activities()
        display_activity_log()

if __name__ == "__main__":
    main()