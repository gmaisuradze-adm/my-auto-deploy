from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'it-inventory-secret-key'
DATABASE = 'inventory.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- AUTH ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['logged_in'] = True
            session['username'] = 'admin'
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- INVENTORY ---
@app.route('/')
@login_required
def index():
    q = request.args.get('q', '')
    conn = get_db_connection()
    if q:
        items = conn.execute('SELECT * FROM inventory WHERE type LIKE ? OR manufacturer LIKE ? OR model LIKE ? OR serial LIKE ? OR owner LIKE ? OR location LIKE ? OR description LIKE ? OR comment LIKE ?',
            tuple(['%' + q + '%'] * 8)).fetchall()
    else:
        items = conn.execute('SELECT * FROM inventory').fetchall()
    conn.close()
    return render_template('index.html', items=items, APP_VERSION="10.9")

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        data = {key: request.form[key] for key in ['type', 'manufacturer', 'model', 'serial', 'status', 'owner', 'install_date', 'location', 'description', 'comment']}
        conn = get_db_connection()
        conn.execute('INSERT INTO inventory (type, manufacturer, model, serial, status, owner, install_date, location, description, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     tuple(data.values()))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
    if not item:
        return redirect(url_for('index'))
    if request.method == 'POST':
        data = {key: request.form[key] for key in ['type', 'manufacturer', 'model', 'serial', 'status', 'owner', 'install_date', 'location', 'description', 'comment']}
        conn.execute('UPDATE inventory SET type=?, manufacturer=?, model=?, serial=?, status=?, owner=?, install_date=?, location=?, description=?, comment=? WHERE id=?',
                     (*data.values(), item_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    conn.close()
    return render_template('edit.html', item=item)

@app.route('/delete/<int:item_id>')
@login_required
def delete(item_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/inventory/update/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update_inventory(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
    if request.method == 'POST':
        new_status = request.form['status']
        new_owner = request.form['owner']
        new_location = request.form['location']
        comment = request.form['comment']
        user = session.get('username', 'system')
        for field, new_val in [('status', new_status), ('owner', new_owner), ('location', new_location)]:
            old_val = item[field]
            if old_val != new_val:
                conn.execute('INSERT INTO changes (inventory_id, field, old_value, new_value, comment, changed_by, change_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
                             (item_id, field, old_val, new_val, comment, user, datetime.now().strftime('%Y-%m-%d %H:%M')))
                conn.execute(f'UPDATE inventory SET {field} = ? WHERE id = ?', (new_val, item_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    conn.close()
    return render_template('update_inventory.html', item=item)

# --- REQUESTS ---
@app.route('/requests/new')
@login_required
def requests_new():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM requests WHERE status = "ახალი" ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('requests_new.html', requests=rows)

@app.route('/requests/done')
@login_required
def requests_done():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM requests WHERE status = "შესრულებულია" ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('requests_done.html', requests=rows)

@app.route('/requests/rejected')
@login_required
def requests_rejected():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM requests WHERE status = "უარყოფილია" ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('requests_rejected.html', requests=rows)

@app.route('/request/add', methods=['GET', 'POST'])
@login_required
def request_add():
    if request.method == 'POST':
        data = {key: request.form[key] for key in ['type', 'quantity', 'description', 'reason', 'location']}
        requested_by = session.get('username')
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M')
        conn = get_db_connection()
        conn.execute('INSERT INTO requests (type, quantity, description, reason, location, requested_by, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (data['type'], data['quantity'], data['description'], data['reason'], data['location'], requested_by, 'ახალი', created_at))
        conn.commit()
        conn.close()
        return redirect(url_for('requests_new'))
    return render_template('request_add.html')

@app.route('/request/<int:req_id>', methods=['GET', 'POST'])
@login_required
def request_view(req_id):
    conn = get_db_connection()
    req = conn.execute('SELECT * FROM requests WHERE id = ?', (req_id,)).fetchone()
    if not req:
        conn.close()
        return redirect(url_for('requests_new'))

    if request.method == 'POST' and req['status'] == 'ახალი':
        action = request.form['action']
        status = 'შესრულებულია' if action == 'done' else 'უარყოფილია'
        assigned_to = session.get('username')
        response = request.form.get('response', '')
        install_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        inventory_id = None

        if action == 'done':
            conn.execute('INSERT INTO inventory (type, status, owner, install_date, location, description, comment) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         (req['type'], 'აქტიური', req['requested_by'], install_date, req['location'], req['description'], f'დამატებულია მოთხოვნიდან #{req_id}'))
            inventory_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        conn.execute('UPDATE requests SET status=?, assigned_to=?, response=?, install_date=?, inventory_id=? WHERE id=?',
                     (status, assigned_to, response, install_date, inventory_id, req_id))
        conn.commit()
        conn.close()
        return redirect(url_for('requests_new'))

    conn.close()
    return render_template('request_view.html', req=req)

# --- PLACEHOLDERS ---


if __name__ == "__main__":
    app.run(debug=True)