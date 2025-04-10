from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from itsdangerous import URLSafeTimedSerializer as Serializer
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Clave secreta para sesiones (idealmente debería guardarse como variable de entorno)
app.secret_key = "elpepe123"

# Configuración de MongoDB Atlas
client = MongoClient("mongodb+srv://ranfy1327:Alejandro123@cluster0.rb48rna.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['db1'] # Nombre de tu base de datos
collection = db['users'] # Nombre de tu colección

# Configuración de SendGrid (idealmente debería guardarse como variable de entorno)
SENDGRID_API_KEY = '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' 

# Serializador para crear y verificar tokens
serializer = Serializer(app.secret_key, salt='password-reset-salt')

# Función para enviar correos
def enviar_email(destinatario, asunto, cuerpo):
    mensaje = Mail(
        from_email='ranfy1327@gmail.com',  # Cambia esto por tu correo
        to_emails=destinatario,
        subject=asunto,
        html_content=cuerpo
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(mensaje)
        print(f"Correo enviado con éxito! Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False

@app.route('/')
def home():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('pagina_principal'))

@app.route('/register', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        email = request.form['email']
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        
        # Verificar si las contraseñas coinciden
        if contrasena != confirmar_contrasena:
            flash("Las contraseñas no coinciden.")
            return redirect(url_for('registro'))
        
        # Verificar si el usuario ya existe
        if collection.find_one({'usuario': usuario}):
            flash("El nombre de usuario ya está en uso.")
            return redirect(url_for('registro'))

        # Verificar si el correo ya está registrado
        if collection.find_one({'email': email}):
            flash("El correo electrónico ya está registrado.")
            return redirect(url_for('registro'))

        # Verificar que se aceptaron los términos y condiciones
        if 'terms' not in request.form:
            flash("Debes aceptar los términos y condiciones.")
            return redirect(url_for('registro'))

        # Hashear la contraseña
        hashed_password = bcrypt.generate_password_hash(contrasena).decode('utf-8')

        # Insertar usuario en la base de datos
        collection.insert_one({
            'usuario': usuario,
            'email': email,
            'contrasena': hashed_password,
            'terms_accepted': True
        })
        
        session['usuario'] = usuario
        return redirect(url_for('pagina_principal'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        # Buscar al usuario en la base de datos
        user = collection.find_one({'usuario': usuario})
        
        # Verificar si las credenciales son correctas
        if user and bcrypt.check_password_hash(user['contrasena'], contrasena):
            session['usuario'] = usuario
            return redirect(url_for('pagina_principal'))
        else:
            flash("Usuario o contraseña incorrectos.")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/pagina_principal')
def pagina_principal():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', usuario=session['usuario'])

@app.route('/mi_perfil')
def mi_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    user_data = collection.find_one({'usuario': usuario})
    return render_template('mi_perfil.html', usuario=user_data['usuario'], email=user_data['email'])

@app.route('/recuperar_contrasena.html', methods=['GET', 'POST'])
def recuperar_contrasena_html():
    return redirect(url_for('recuperar_contrasena'))

@app.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        usuario = collection.find_one({'email': email})

        if usuario:
            token = serializer.dumps(email, salt='password-reset-salt')
            enlace = url_for('restablecer_contrasena', token=token, _external=True)
            asunto = "Recuperación de contraseña"
            cuerpo = f"""
            <p>Hola, hemos recibido una solicitud para restablecer tu contraseña.</p>
            <p>Si no has solicitado este cambio, ignora este mensaje.</p>
            <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
            <a href="{enlace}">Restablecer contraseña</a>
            """
            if enviar_email(email, asunto, cuerpo):
                flash("Te hemos enviado un correo para recuperar tu contraseña.", "success")
            else:
                flash("Hubo un problema al enviar el correo. Inténtalo de nuevo más tarde.", "error")
        else:
            flash("El correo electrónico no está registrado.", "error")

    return render_template('recuperar_contrasena.html')

@app.route('/restablecer_contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash("El enlace de restablecimiento ha caducado o es inválido.", "error")
        return redirect(url_for('recuperar_contrasena'))

    if request.method == 'POST':
        nueva_contrasena = request.form['nueva_contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        
        # Verificar si las contraseñas coinciden
        if nueva_contrasena != confirmar_contrasena:
            flash("Las contraseñas no coinciden.")
            return render_template('restablecer_contrasena.html')
            
        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
        collection.update_one({'email': email}, {'$set': {'contrasena': hashed_password}})
        flash("Tu contraseña ha sido restablecida con éxito.", "success")
        return redirect(url_for('login'))

    return render_template('restablecer_contrasena.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))