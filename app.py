#imports
from flask import Flask, render_template, redirect, request, flash, Response
import csv
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

#app configuration
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key_here'  # Needed for flashing messages
Scss(app)

#database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#models
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<Contact {self.id}>'

with app.app_context():
    db.create_all()

# Home page route
@app.route('/', methods=['POST', 'GET'])
def index():
    search_query = request.args.get('search', '')
    if request.method == 'POST':
        name = request.form['name']
        number = request.form['number']
        # Check for duplicate
        duplicate = Contact.query.filter_by(name=name, number=number).first()
        if duplicate:
            flash("A contact with this name and number already exists.", 'danger')
            return redirect('/')
        new_contact = Contact(name=name, number=number)
        try:
            db.session.add(new_contact)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            flash(f"Error adding contact: {e}", 'danger')
            return redirect('/')
    else:
        if search_query:
            contacts = Contact.query.filter(Contact.name.ilike(f"%{search_query}%")).order_by(Contact.name.asc()).all()
        else:
            contacts = Contact.query.order_by(Contact.name.asc()).all()
        return render_template('index.html', contacts=contacts, search_query=search_query)

# Delete contact
@app.route('/delete/<int:id>', methods=['GET'])
def delete(id: int):
    contact = Contact.query.get_or_404(id)
    try:
        db.session.delete(contact)
        
        db.session.commit()
        return redirect('/')
    except Exception as e:
        flash(f"Error deleting contact: {e}", 'danger')
        return redirect('/')

# Update contact
@app.route('/update/<int:id>', methods=['POST', 'GET'])
def update(id: int):
    contact = Contact.query.get_or_404(id)
    if request.method == 'POST':
        contact.name = request.form['name']
        contact.number = request.form['number']
        try:
            db.session.commit()
            return redirect('/')
        except Exception as e:
            flash(f"Error updating contact: {e}", 'danger')
            return redirect(f'/update/{id}')
    else:
        return render_template('update.html', contact=contact)

@app.route('/export', methods=['GET'])
def export_contacts():
    contacts = Contact.query.order_by(Contact.name.asc()).all()
    def generate():
        data = [['ID', 'Name', 'Number', 'Created At']]
        for c in contacts:
            data.append([c.id, c.name, c.number, c.created_at.strftime('%Y-%m-%d %H:%M:%S')])
        output = []
        writer = csv.writer(output)
        for row in data:
            writer.writerow(row)
        return '\r\n'.join([','.join(map(str, row)) for row in data])
    csv_data = generate()
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=contacts.csv'
        }
    )

if __name__ == '__main__':
    app.run(debug=True)