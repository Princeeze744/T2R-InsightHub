import sqlite3
import pandas as pd
from datetime import date, datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from fpdf import FPDF

class T2RDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('t2r_data.db', check_same_thread=False)
        self.create_tables()
        self.initialize_performance_columns()
        
    def create_tables(self):
        # Create students table with performance fields
        self.conn.execute('''CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            program TEXT CHECK(program IN ('AI', 'Beginner', 'Gold', 'VIP')),
            join_date DATE,
            payment_status TEXT CHECK(payment_status IN ('Paid', 'Partial', 'Unpaid')),
            amount_paid REAL,
            source TEXT,
            assessment_score INTEGER DEFAULT 0,
            risk_score INTEGER DEFAULT 0,
            performance_rating INTEGER DEFAULT 0
        )''')

        # Marketing table
        self.conn.execute('''CREATE TABLE IF NOT EXISTS marketing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            campaign_name TEXT,
            start_date DATE,
            end_date DATE,
            spend REAL,
            leads_generated INTEGER
        )''')
        
        # Payment history table
        self.conn.execute('''CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            amount REAL,
            payment_date DATE,
            method TEXT,
            transaction_id TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )''')
        
        # Audit log table
        self.conn.execute('''CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        self.conn.commit()
    
    def initialize_performance_columns(self):
        """Ensure performance columns exist with default values"""
        cursor = self.conn.execute("PRAGMA table_info(students)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'assessment_score' not in columns:
            self.conn.execute("ALTER TABLE students ADD COLUMN assessment_score INTEGER DEFAULT 0")
        if 'risk_score' not in columns:
            self.conn.execute("ALTER TABLE students ADD COLUMN risk_score INTEGER DEFAULT 0")
        if 'performance_rating' not in columns:
            self.conn.execute("ALTER TABLE students ADD COLUMN performance_rating INTEGER DEFAULT 0")
            
        self.conn.commit()
        
    def log_audit(self, user, action):
        self.conn.execute('''INSERT INTO audit_log (user, action)
                          VALUES (?, ?)''', (user, action))
        self.conn.commit()

    # Student methods
    def add_student(self, name, email, phone, program, payment_status, amount_paid, source):
        self.conn.execute('''INSERT INTO students (name, email, phone, program, join_date, payment_status, amount_paid, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
            (name, email, phone, program, date.today(), payment_status, amount_paid, source))
        self.conn.commit()
        self.log_audit("System", f"Added student: {name}")

    def update_student_performance(self, student_id, assessment_score, risk_score, performance_rating):
        self.conn.execute('''UPDATE students 
                          SET assessment_score = ?, risk_score = ?, performance_rating = ?
                          WHERE id = ?''', 
                          (assessment_score, risk_score, performance_rating, student_id))
        self.conn.commit()
        self.log_audit("System", f"Updated performance for student ID: {student_id}")
        
    def get_students(self):
        df = pd.read_sql("SELECT * FROM students", self.conn)
        
        # Ensure performance columns exist in the DataFrame
        for col in ['assessment_score', 'risk_score', 'performance_rating']:
            if col not in df.columns:
                df[col] = 0
                
        return df

    def delete_student(self, student_id):
        self.conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        self.conn.execute("DELETE FROM payments WHERE student_id = ?", (student_id,))
        self.conn.commit()
        self.log_audit("System", f"Deleted student ID: {student_id}")

    # Campaign methods
    def add_campaign(self, platform, campaign_name, start_date, end_date, spend, leads_generated):
        self.conn.execute('''INSERT INTO marketing (platform, campaign_name, start_date, end_date, spend, leads_generated)
            VALUES (?, ?, ?, ?, ?, ?)''', 
            (platform, campaign_name, start_date, end_date, spend, leads_generated))
        self.conn.commit()
        self.log_audit("System", f"Added campaign: {campaign_name}")

    def get_campaigns(self):
        return pd.read_sql("SELECT * FROM marketing", self.conn)
    
    def delete_campaign(self, campaign_id):
        self.conn.execute("DELETE FROM marketing WHERE id = ?", (campaign_id,))
        self.conn.commit()
        self.log_audit("System", f"Deleted campaign ID: {campaign_id}")

    # Payment methods
    def get_payments(self):
        return pd.read_sql("SELECT * FROM payments", self.conn)

    def record_payment(self, student_id, amount, method="Bank Transfer", transaction_id=""):
        # Record payment
        self.conn.execute('''INSERT INTO payments (student_id, amount, payment_date, method, transaction_id)
                          VALUES (?, ?, ?, ?, ?)''', 
                          (student_id, amount, date.today(), method, transaction_id))
        
        # Update student payment status
        student = self.get_student(student_id)
        program_price = self.get_program_price(student['program'])
        total_paid = self.get_total_paid(student_id) + amount
        
        if total_paid >= program_price:
            status = 'Paid'
        elif total_paid > 0:
            status = 'Partial'
        else:
            status = 'Unpaid'
            
        self.conn.execute('''UPDATE students 
                          SET amount_paid = ?, payment_status = ?
                          WHERE id = ?''', (total_paid, status, student_id))
        self.conn.commit()
        self.log_audit("System", f"Recorded payment for student ID: {student_id}")
        
    def delete_payment(self, payment_id):
        self.conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
        self.conn.commit()
        self.log_audit("System", f"Deleted payment ID: {payment_id}")
        
        # Recalculate student status
        student_id = self.conn.execute("SELECT student_id FROM payments WHERE id = ?", (payment_id,)).fetchone()
        if student_id:
            student_id = student_id[0]
            student = self.get_student(student_id)
            total_paid = self.get_total_paid(student_id)
            program_price = self.get_program_price(student['program'])
            
            if total_paid >= program_price:
                status = 'Paid'
            elif total_paid > 0:
                status = 'Partial'
            else:
                status = 'Unpaid'
                
            self.conn.execute('''UPDATE students 
                              SET amount_paid = ?, payment_status = ?
                              WHERE id = ?''', (total_paid, status, student_id))
        self.conn.commit()
    
    def get_student(self, student_id):
        cursor = self.conn.execute('''SELECT * FROM students WHERE id = ?''', (student_id,))
        columns = [col[0] for col in cursor.description]
        student_row = cursor.fetchone()
        
        if not student_row:
            return None
            
        # Ensure performance columns exist in the student dict
        student = dict(zip(columns, student_row))
        for col in ['assessment_score', 'risk_score', 'performance_rating']:
            if col not in student:
                student[col] = 0
                
        return student
    
    def get_program_price(self, program):
        prices = {'AI': 497, 'Beginner': 297, 'Gold': 1297, 'VIP': 2997}
        return prices.get(program, 0)
    
    def get_total_paid(self, student_id):
        cursor = self.conn.execute('''SELECT COALESCE(SUM(amount), 0) 
                                   FROM payments WHERE student_id = ?''', (student_id,))
        return cursor.fetchone()[0]
    
    # ROI calculation
    def calculate_roi(self):
        students = self.get_students()
        campaigns = self.get_campaigns()

        program_prices = {'AI': 497, 'Beginner': 297, 'Gold': 1297, 'VIP': 2997}
        students['program_value'] = students['program'].map(program_prices)

        roi_data = []
        for source in students['source'].unique():
            source_students = students[students['source'] == source]
            total_revenue = source_students['amount_paid'].sum()
            
            source_campaigns = campaigns[campaigns['platform'] == source]
            total_spend = source_campaigns['spend'].sum()
            
            roi = (total_revenue - total_spend) / total_spend * 100 if total_spend else 0
            roi_data.append({
                'source': source,
                'students': len(source_students),
                'revenue': total_revenue,
                'spend': total_spend,
                'roi': roi
            })
        return pd.DataFrame(roi_data)
    
    # Reporting
    def generate_report(self, report_type='monthly'):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Report header
        pdf.cell(200, 10, txt=f"Trade2Retire Academy {report_type.capitalize()} Report", 
                ln=True, align='C')
        pdf.ln(10)
        
        # Financial summary
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Financial Summary", ln=True)
        pdf.set_font("Arial", size=10)
        
        # Get financial data
        students = self.get_students()
        revenue = students['amount_paid'].sum()
        campaigns = self.get_campaigns()
        spend = campaigns['spend'].sum()
        
        pdf.cell(200, 10, txt=f"Total Revenue: ${revenue:,.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Marketing Spend: ${spend:,.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Net Profit: ${revenue - spend:,.2f}", ln=True)
        pdf.ln(10)
        
        # Program breakdown
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Program Performance", ln=True)
        pdf.set_font("Arial", size=10)
        
        program_revenue = students.groupby('program')['amount_paid'].sum()
        for program, rev in program_revenue.items():
            pdf.cell(200, 10, txt=f"{program}: ${rev:,.2f}", ln=True)
        
        # Student performance
        if 'assessment_score' in students.columns:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Student Performance", ln=True)
            pdf.set_font("Arial", size=10)
            
            avg_score = students['assessment_score'].mean()
            pdf.cell(200, 10, txt=f"Average Assessment Score: {avg_score:.1f}/100", ln=True)
            
            top_performers = students.sort_values('assessment_score', ascending=False).head(3)
            pdf.cell(200, 10, txt="Top Performers:", ln=True)
            for i, row in top_performers.iterrows():
                pdf.cell(200, 10, txt=f"{row['name']} - {row['program']} ({row['assessment_score']}/100)", ln=True)
        
        # Save the report
        filename = f"T2R_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf.output(filename)
        return filename
    
    # Student success prediction
    def predict_student_success(self):
        students = self.get_students()
        if len(students) < 10:
            return pd.DataFrame()  # Not enough data
        
        # Prepare features
        features = students[['assessment_score', 'risk_score', 'performance_rating']].copy()
        
        # Create target (success = high assessment score and performance rating)
        students['success'] = ((students['assessment_score'] >= 80) & 
                              (students['performance_rating'] >= 4)).astype(int)
        
        # Train model
        X_train, X_test, y_train, y_test = train_test_split(
            features, students['success'], test_size=0.2, random_state=42
        )
        
        model = RandomForestClassifier()
        model.fit(X_train, y_train)
        
        # Make predictions
        students['success_prediction'] = model.predict_proba(features)[:, 1]
        return students[['name', 'email', 'success_prediction']].sort_values('success_prediction', ascending=False)
    
    # Database management
    def reset_database(self):
        self.conn.execute("DROP TABLE IF EXISTS students")
        self.conn.execute("DROP TABLE IF EXISTS marketing")
        self.conn.execute("DROP TABLE IF EXISTS payments")
        self.conn.execute("DROP TABLE IF EXISTS audit_log")
        self.create_tables()
        self.initialize_performance_columns()
        self.log_audit("System", "Database reset")
    
    def backup_database(self):
        backup_file = f"t2r_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        with open(backup_file, 'wb') as f:
            for line in self.conn.iterdump():
                f.write(f'{line}\n'.encode('utf-8'))
        self.log_audit("System", f"Created backup: {backup_file}")
        return backup_file
    
    def restore_database(self, backup_file):
        self.reset_database()
        with open(backup_file, 'r') as f:
            sql = f.read()
            self.conn.executescript(sql)
        self.conn.commit()
        self.log_audit("System", f"Restored from backup: {backup_file}")