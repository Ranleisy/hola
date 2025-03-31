from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from itsdangerous import URLSafeTimedSerializer as Serializer
import os
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
bcrypt = Bcrypt(app)

# Clave secreta para sesiones (idealmente debería guardarse como variable de entorno)
app.secret_key = os.environ.get('SECRET_KEY', "elpepe123")

# Configuración de MongoDB Atlas
MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://ranfy1327:Alejandro123@cluster0.rb48rna.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['db1'] # Nombre de tu base de datos
collection = db['users'] # Nombre de tu colección

# Configuración de SendGrid (idealmente debería guardarse como variable de entorno)
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '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')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'ranfy1327@gmail.com')

# Serializador para crear y verificar tokens
serializer = Serializer(app.secret_key, salt='password-reset-salt')

# Función para enviar correos
def enviar_email(destinatario, asunto, cuerpo):
    mensaje = Mail(
        from_email=FROM_EMAIL,
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
    if 'usuario' in session:
        return redirect(url_for('pagina_principal'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        email = request.form['email']
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        
        # Verificar si las contraseñas coinciden
        if contrasena != confirmar_contrasena:
            flash("Las contraseñas no coinciden.", "error")
            return render_template('register.html')
        
        # Verificar si el usuario ya existe
        if collection.find_one({'usuario': usuario}):
            flash("El nombre de usuario ya está en uso.", "error")
            return render_template('register.html')

        # Verificar si el correo ya está registrado
        if collection.find_one({'email': email}):
            flash("El correo electrónico ya está registrado.", "error")
            return render_template('register.html')

        # Verificar que se aceptaron los términos y condiciones
        if 'terms' not in request.form:
            flash("Debes aceptar los términos y condiciones.", "error")
            return render_template('register.html')

        # Hashear la contraseña
        hashed_password = bcrypt.generate_password_hash(contrasena).decode('utf-8')

        # Insertar usuario en la base de datos
        collection.insert_one({
            'usuario': usuario,
            'email': email,
            'contrasena': hashed_password,
            'terms_accepted': True,
            'fecha_registro': datetime.now().strftime("%d/%m/%Y")
        })
        
        session['usuario'] = usuario
        flash("¡Registro exitoso! Bienvenido a FastHelp.", "success")
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
            flash("Usuario o contraseña incorrectos.", "error")
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
    
    # Asegurarse de que fecha_registro existe
    fecha_registro = user_data.get('fecha_registro', 'No disponible')
    
    return render_template('mi_perfil.html', 
                          usuario=user_data['usuario'], 
                          email=user_data['email'],
                          fecha_registro=fecha_registro)

@app.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        usuario = collection.find_one({'email': email})

        if usuario:
            token = serializer.dumps(email, salt='password-reset-salt')
            enlace = url_for('restablecer_contrasena', token=token, _external=True)
            asunto = "Recuperación de contraseña - FastHelp"
            cuerpo = f"""
            <p>Hola {usuario['usuario']}, hemos recibido una solicitud para restablecer tu contraseña.</p>
            <p>Si no has solicitado este cambio, ignora este mensaje.</p>
            <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
            <a href="{enlace}">Restablecer contraseña</a>
            <p>Este enlace expirará en 1 hora.</p>
            <p>Saludos,<br>El equipo de FastHelp</p>
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
            flash("Las contraseñas no coinciden.", "error")
            return render_template('restablecer_contrasena.html')
            
        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
        collection.update_one({'email': email}, {'$set': {'contrasena': hashed_password}})
        flash("Tu contraseña ha sido restablecida con éxito.", "success")
        return redirect(url_for('login'))

    return render_template('restablecer_contrasena.html')

# Rutas para manejar las redirecciones de los templates
@app.route('/templates/<path:template_path>')
def handle_template_redirect(template_path):
    # Mapeo de rutas de templates a rutas de la aplicación
    template_routes = {
        'login.html': 'login',
        'register.html': 'registro',
        'recuperar_contrasena.html': 'recuperar_contrasena',
        'reestablecer_contrasena.html': 'recuperar_contrasena',
        'mi_perfil.html': 'mi_perfil',
        'index.html': 'pagina_principal'
    }
    
    if template_path in template_routes:
        return redirect(url_for(template_routes[template_path]))
    
    # Si no se encuentra en el mapeo, intentar renderizar directamente
    try:
        return render_template(template_path)
    except:
        return redirect(url_for('pagina_principal'))

# Rutas adicionales
@app.route('/servicios')
def servicios():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('servicios.html', usuario=session['usuario'])

@app.route('/profesionales')
def profesionales():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('profesionales.html', usuario=session['usuario'])

@app.route('/como-funciona')
def como_funciona():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('como_funciona.html', usuario=session['usuario'])

@app.route('/mis_servicios')
def mis_servicios():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('mis_servicios.html', usuario=session['usuario'])

@app.route('/solicitar-servicio')
def solicitar_servicio():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('solicitar_servicio.html', usuario=session['usuario'])

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Usar variables de entorno para el puerto si está disponible (para hosting)
    port = int(os.environ.get('PORT', 5000))
    # En producción, es mejor no usar debug=True
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)