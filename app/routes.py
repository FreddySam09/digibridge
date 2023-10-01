from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from app import app, db, login_manager, save_thumbnail, save_video
from app.models import User, ComputerBooking, Doubt, Reply, Staff, Query
from app.forms import SignupForm, LoginForm, StaffSignupForm, StaffLoginForm, QueryForm
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from datetime import datetime, timedelta
from flask_login import current_user, logout_user
from flask_migrate import Migrate


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return user

    staff = Staff.query.get(int(user_id))
    if staff:
        return staff

    return None  

@app.route('/')
def welcome():
    return render_template('welcome.html',user=current_user)

@app.route('/about')
def about():
    return render_template('about.html', user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        new_user = User(name=form.name.data, email=form.email.data, password=form.password.data, user_type='user')
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form, user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.password == form.password.data:
            logout_user()
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Please check your credentials.', 'danger')

    return render_template('login.html', form=form,user=current_user)

from flask import session

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  
    flash('Logged out successfully.', 'success')
    return redirect(url_for('welcome'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/pre-booking', methods=['GET', 'POST'])
def pre_booking():
    if request.method == 'POST':
        selected_slot = request.form.get('slot')
        return redirect(url_for('computer_booking', slot=selected_slot))

    
    min_booking_date = datetime.now().date() - timedelta(days=2)

    if current_user.last_booking_date and current_user.last_booking_date >= min_booking_date:
        flash('You cannot book a computer within the next 2 days.', 'danger')
        return redirect(url_for('home'))

    
    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]
    
    return render_template('days.html', dates=dates)

@app.route('/pre-booking/<selected_date>', methods=['GET', 'POST'])
def pre_booking_slots(selected_date):
    available_slots = ['Slot 1', 'Slot 2', 'Slot 3', 'Slot 4']  
    booked_computers = {}  

    for slot in available_slots:
        booked_computers[slot] = []

    
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()  
    booked_records = ComputerBooking.query.filter_by(booking_date=selected_date_obj).all()

    for record in booked_records:
        booked_computers[record.slot].append(record.computer)

    
    slot_timings = {
        'Slot 1': '9 - 11 AM',
        'Slot 2': '12 - 2 PM',
        'Slot 3': '3 - 5 PM',
        'Slot 4': '6 - 8 PM'
    }

    if request.method == 'POST':
        selected_slot = request.form.get('slot')
        if current_user.is_authenticated:
            if selected_slot in booked_computers and any(current_user.name in booked_computers[slot] for slot in booked_computers):
                flash(f'You have already booked a computer for slot {selected_slot} of {selected_date}.', 'danger')
            else:
                return redirect(url_for('computer_booking', slot=selected_slot, date=selected_date))

    
    for i in range(1, 8):  
        next_date_obj = selected_date_obj + timedelta(days=i)
        next_date = next_date_obj.strftime('%Y-%m-%d')

        next_booked_records = ComputerBooking.query.filter_by(booking_date=next_date_obj).all()

        if not all(slot in booked_computers and len(booked_computers[slot]) >= len(available_slots) for slot in available_slots):
            
            break

    if i == 7:
        flash('No available slots found for the next 7 days.', 'danger')
        return redirect(url_for('home'))

    return render_template('pre_booking.html', slots=available_slots, booked_computers=booked_computers, selected_date=selected_date, next_available_date=next_date, slot_timings=slot_timings)

from flask_login import current_user, login_required

@app.route('/computer-booking/<slot>/<date>', methods=['GET', 'POST'])
@login_required
def computer_booking(slot, date):
    booking_date = datetime.strptime(date, '%Y-%m-%d').date()

    min_booking_date = datetime.now().date() - timedelta(days=2)
    if current_user.last_booking_date and current_user.last_booking_date >= min_booking_date:
        flash('You cannot book a computer within the next 2 days.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        selected_computer = request.form.get('computer')
        existing_booking = ComputerBooking.query.filter_by(booking_date=booking_date, slot=slot, computer=selected_computer).first()

        if existing_booking:
            flash(f'Computer system {selected_computer} is already booked for slot {slot} of {existing_booking.booking_date} by {existing_booking.booked_by}.', 'danger')
        else:
            new_booking = ComputerBooking(
                user_id=current_user.id,
                booking_date=booking_date,
                slot=slot,
                computer=selected_computer,
                booked_by=current_user.name
            )
            db.session.add(new_booking)
            db.session.commit()

            current_user.last_booking_date = booking_date
            db.session.commit()

            # Redirect to the payment confirmation page
            return redirect(url_for('payment_confirmation', booking_id=new_booking.id))

    available_computers = get_available_computers(slot, booking_date)

    return render_template('computer_booking.html', slot=slot, booking_date=booking_date, available_computers=available_computers)


def get_available_computers(slot, booking_date):
    booked_computers = ComputerBooking.query.filter_by(booking_date=booking_date, slot=slot).all()
    all_computers = ['System 1', 'System 2', 'System 3', 'System 4', 'System 5', 'System 6']
    
    available_computers = []

    for computer in all_computers:
        booking_info = {'name': computer, 'is_available': True, 'booked_by': None}
        for booking in booked_computers:
            if booking.computer == computer:
                booking_info['is_available'] = False
                booking_info['booked_by'] = booking.booked_by
                break
        available_computers.append(booking_info)

    return available_computers



@app.route('/help', methods=['GET', 'POST'])
@login_required
def help():
    doubts = Doubt.query.all()

    if request.method == 'POST':
        doubt_text = request.form.get('doubt')
        if doubt_text is not None:  
            new_doubt = Doubt(text=doubt_text)
            db.session.add(new_doubt)
            db.session.commit()

        for doubt in doubts:
            reply_key = str(doubt.id)
            reply_text = request.form.get(reply_key)
            if reply_text is not None:  
                new_reply = Reply(text=reply_text, doubt_id=doubt.id)
                db.session.add(new_reply)

        db.session.commit()  

    return render_template('help.html', doubts=doubts)

@app.route('/professional-help', methods=['GET', 'POST'])
@login_required  
def professional_help():
    departments = [('Maths', 'Maths'), ('Physics', 'Physics'), ('Chemistry', 'Chemistry'), ('Biology', 'Biology')]
    selected_department = request.form.get('department')

    if selected_department:
        staff_members = Staff.query.filter_by(department=selected_department).all()
    else:
        staff_members = []

    user_queries = Query.query.filter_by(user_id=current_user.id).all() 

    return render_template('professional_help.html', departments=departments, staff_members=staff_members, user_queries=user_queries)


@app.route('/query-staff/<int:staff_id>', methods=['GET', 'POST'])
@login_required
def query_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    form = QueryForm()

    if form.validate_on_submit():
        new_query = Query(user_id=current_user.id, staff_id=staff.id, query_text=form.query.data)
        db.session.add(new_query)
        db.session.commit()
        flash('Your query has been submitted.', 'success')
        return redirect(url_for('professional_help'))

    return render_template('query_staff.html', staff=staff, form=form)


@app.route('/staff-signup', methods=['GET', 'POST'])
def staff_signup():
    form = StaffSignupForm()

    if form.validate_on_submit():
        existing_staff = Staff.query.filter_by(email=form.email.data).first()

        if existing_staff:
            flash('Email already registered. Please log in or use a different email.', 'danger')
            return redirect(url_for('staff_login'))

        new_staff = Staff(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data,
            department=form.department.data,
            phone_number=form.phone_number.data,
            user_type='staff'
        )
        db.session.add(new_staff)
        db.session.commit()
        flash('Staff account created successfully. Please log in.', 'success')
        return redirect(url_for('staff_login'))

    return render_template('staff_signup.html', form=form)


@app.route('/staff-login', methods=['GET', 'POST'])
def staff_login():
    form = StaffLoginForm()

    if form.validate_on_submit():
        staff = Staff.query.filter_by(email=form.email.data).first()

        if staff and staff.password == form.password.data:
            logout_user()
            login_user(staff)  
            flash('Logged in successfully!', 'success')
            return redirect(url_for('staff_home'))  
        else:
            flash('Login failed. Please check your credentials.', 'danger')

    return render_template('staff_login.html', form=form)

@app.route('/staff-home')
@login_required
def staff_home():
    if current_user.user_type == 'staff':
        return render_template('staff_home.html', user=current_user)
    else:
        flash('Access denied. You are not authorized to access this page.', 'danger')
        return redirect(url_for('home'))  

@app.route('/staff-queries', methods=['GET', 'POST'])
@login_required
def staff_queries():
    if current_user.user_type == 'staff':
        staff = current_user
        queries = Query.query.filter_by(staff_id=staff.id).all()

        if request.method == 'POST':
            response = request.form.get('response')
            query_id = int(request.form.get('query_id'))

            query = Query.query.get(query_id)
            query.response_text = response
            db.session.commit()
            flash('Response sent successfully.', 'success')

        return render_template('staff_queries.html', queries=queries)
    else:
        flash('Access denied. You are not authorized to access this page.', 'danger')
        return redirect(url_for('staff_home'))

@app.route('/payment-confirmation')
@login_required
def payment_confirmation():
    booking_id = request.args.get('booking_id')  # Get the booking_id from the URL parameters
    booking = ComputerBooking.query.get(booking_id)
    if booking:
        booking.status = 'booked'  # Update the status to 'booked'
        db.session.commit()

    return render_template('payment_confirmation.html', booking=booking)

#haha

from flask import render_template, redirect, url_for, request, send_from_directory
from flask_login import login_required, current_user
from .models import Course, db
from .forms import NewCourseForm

@app.route('/courses', methods=['GET'])
@login_required
def courses():
    subject_filter = request.args.get('subject')  # Get subject filter from the URL

    if subject_filter:
        courses = Course.query.filter_by(subject=subject_filter).all()
    else:
        courses = Course.query.all()

    return render_template('courses.html', courses=courses)

@app.route('/take_course/<int:course_id>')
@login_required
def take_course(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('course_detail.html', course=course)

from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

@app.route('/new_course', methods=['GET', 'POST'])
@login_required
def new_course():
    form = NewCourseForm()

    # Get the department of the currently logged-in staff member
    staff_department = Staff.query.filter_by(id=current_user.id).first().department

    # Populate the choices for the "Subject" field with the staff's department
    form.subject.choices = [(staff_department, staff_department)]

    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        subject = form.subject.data
        thumbnail = save_thumbnail(form.thumbnail.data)
        video = save_video(form.video.data)

        course = Course(title=title, description=description, subject=subject, thumbnail_filename=thumbnail, video_filename=video, staff_id=current_user.id)
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully', 'success')
        return redirect(url_for('your_courses'))
    
    return render_template('new_course.html', form=form)

@app.route('/your_courses')
@login_required
def your_courses():
    courses = current_user.courses
    return render_template('your_courses.html', courses=courses)

from .forms import EditCourseForm  # You need to create an EditCourseForm similar to NewCourseForm

@app.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if course.staff_id != current_user.id:
        flash('You do not have permission to edit this course.', 'danger')
        return redirect(url_for('your_courses'))

    if request.method == 'POST':
        course.title = request.form['title']
        course.description = request.form['description']

        # Handle file uploads for thumbnail and video
        if 'thumbnail' in request.files:
            thumbnail = request.files['thumbnail']
            if thumbnail.filename != '':
                thumbnail_filename = secure_filename(thumbnail.filename)
                thumbnail.save(os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename))
                course.thumbnail = thumbnail_filename
        
        if 'video' in request.files:
            video = request.files['video']
            if video.filename != '':
                video_filename = secure_filename(video.filename)
                video.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))
                course.video = video_filename

        db.session.commit()
        flash('Course updated successfully', 'success')
        return redirect(url_for('your_courses'))

    return render_template('edit_course.html', course=course)

@app.route('/delete_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def delete_course(course_id):
    course = Course.query.get(course_id)
    if not course:
        flash('Course not found', 'danger')
        return redirect(url_for('your_courses'))

    # Check if the course belongs to the current user (staff)
    if course.staff_id != current_user.id:
        flash('You do not have permission to delete this course', 'danger')
        return redirect(url_for('your_courses'))

    if request.method == 'POST':
        # Delete the course from the database
        db.session.delete(course)
        db.session.commit()

        flash('Course deleted successfully', 'success')
        return redirect(url_for('your_courses'))

    return render_template('delete_course.html', course=course)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/course_list', methods=['GET'])
@login_required
def course_list():
    

    return render_template('course_list.html')

# Define the route for taking a lesson
@app.route('/math', methods=['GET'])
def math():
    

    # Render the take_lesson.html template with the course details
    return render_template('math.html')

# Define the route for taking a test
@app.route('/mathtest', methods=['GET'])
def mathtest():
    

    # Render the take_test.html template with the course details
    return render_template('test.html')

# Define the route for taking a lesson
@app.route('/chem', methods=['GET'])
def chem():
    

    # Render the take_lesson.html template with the course details
    return render_template('chem.html')

# Define the route for taking a test
@app.route('/chemtest', methods=['GET'])
def chemtest():
    

    # Render the take_test.html template with the course details
    return render_template('test.html')

@app.route('/excel', methods=['GET'])
def excel():
    

    # Render the take_lesson.html template with the course details
    return render_template('excel.html')

# Define the route for taking a test
@app.route('/exceltest', methods=['GET'])
def exceltest():
    

    # Render the take_test.html template with the course details
    return render_template('test.html')

@app.route('/ppt', methods=['GET'])
def ppt():
    

    # Render the take_lesson.html template with the course details
    return render_template('ppt.html')