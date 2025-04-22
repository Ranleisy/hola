from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from itsdangerous import URLSafeTimedSerializer as Serializer
import os
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app
import ssl


# Configuración de la aplicación Flask
app = Flask(__name__)
bcrypt = Bcrypt(app)

# Clave secreta para sesiones (idealmente debería guardarse como variable de entorno)
app.secret_key = os.environ.get('SECRET_KEY', "elpepe123")

# Configuración de MongoDB Atlas
MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://ranfy1327:Alejandro123@cluster0.rb48rna.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['db1']
collection = db['users']

# Configuración de SendGrid
SENDGRID_API_KEY = os.environ.get('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', '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')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'ranfy1327@gmail.com')
ssl._create_default_https_context = ssl._create_unverified_context

# Serializador
serializer = Serializer(app.secret_key, salt='password-reset-salt')

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'img')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}

# Función para enviar correo
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
    
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'img')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    if 'usuario' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        email = request.form['email']
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        
        if contrasena != confirmar_contrasena:
            flash("Las contraseñas no coinciden.", "error")
            return render_template('register.html')
        
        if collection.find_one({'usuario': usuario}):
            flash("El nombre de usuario ya está en uso.", "error")
            return render_template('register.html')

        if collection.find_one({'email': email}):
            flash("El correo electrónico ya está registrado.", "error")
            return render_template('register.html')

        if 'terms' not in request.form:
            flash("Debes aceptar los términos y condiciones.", "error")
            return render_template('register.html')

        hashed_password = bcrypt.generate_password_hash(contrasena).decode('utf-8')
        jefe_existente = collection.find_one({'tipo_usuario': 'jefe'})
        tipo_usuario = 'cliente'
        if not jefe_existente:
            tipo_usuario = 'jefe'

        collection.insert_one({
            'usuario': usuario,
            'email': email,
            'contrasena': hashed_password,
            'terms_accepted': True,
            'fecha_registro': datetime.now().strftime("%d/%m/%Y"),
            'tipo_usuario': tipo_usuario
        })

        session['usuario'] = usuario
        session['tipo_usuario'] = tipo_usuario
        flash(f"¡Registro exitoso como {tipo_usuario.capitalize()}!", "success")
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/register_employee', methods=['GET', 'POST'])
def register_employee():
    if 'usuario' not in session or session.get('tipo_usuario') != 'jefe':
        flash("Solo el jefe puede registrar empleados.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        usuario = request.form['usuario']
        apellido = request.form['apellido']
        cedula = request.form['cedula']
        telefono = request.form['telefono']
        email = request.form['email']
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        cargo = request.form['cargo']

        if contrasena != confirmar_contrasena:
            flash("Las contraseñas no coinciden.", "error")
            return render_template('register_employee.html')

        if collection.find_one({'usuario': usuario}):
            flash("El nombre de usuario ya está en uso.", "error")
            return render_template('register_employee.html')

        if collection.find_one({'email': email}):
            flash("El correo electrónico ya está registrado.", "error")
            return render_template('register_employee.html')

        hashed_password = bcrypt.generate_password_hash(contrasena).decode('utf-8')

        collection.insert_one({
            'usuario': usuario,
            'apellido': apellido,
            'cedula': cedula,
            'telefono': telefono,
            'email': email,
            'cargo': cargo,
            'contrasena': hashed_password,
            'fecha_registro': datetime.now().strftime("%d/%m/%Y"),
            'tipo_usuario': 'empleado',
            'salario_base': 1000,
            'horas_extra': 0
        })

        flash("Empleado registrado exitosamente.", "success")
        return redirect(url_for('index'))

    return render_template('register_employee.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        
        user = collection.find_one({'usuario': usuario})
        if user and bcrypt.check_password_hash(user['contrasena'], contrasena):
            session['usuario'] = usuario
            session['tipo_usuario'] = user.get('tipo_usuario', 'cliente')
            flash(f"Bienvenido {session['tipo_usuario'].capitalize()}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrectos.", "error")
            return render_template('login.html')
    return render_template('login.html')

@app.route('/index')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', 
        usuario=session['usuario'], 
        tipo_usuario=session.get('tipo_usuario', 'cliente')
    )

@app.route('/pagina_principal')
def pagina_principal():
    if 'usuario' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/mi_perfil')
def mi_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    user_data = collection.find_one({'usuario': usuario})
    if not user_data:
        flash("Error al obtener los datos del usuario", "error")
        return redirect(url_for('index'))

    fecha_registro = user_data.get('fecha_registro', 'No disponible')
    return render_template('mi_perfil.html', 
        usuario=user_data['usuario'], 
        email=user_data['email'],
        telefono=user_data.get('telefono', ''),
        direccion=user_data.get('direccion', ''),
        tipo_usuario=user_data.get('tipo_usuario', 'Cliente'),
        fecha_registro=fecha_registro)

@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'usuario' not in session:
        flash("Debes iniciar sesión para editar tu perfil", "error")
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    user_data = collection.find_one({'usuario': usuario})
    if not user_data:
        flash("Error al obtener los datos del usuario", "error")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form['email']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        existing_email = collection.find_one({'email': email, 'usuario': {'$ne': usuario}})
        if existing_email:
            flash("El correo electrónico ya está registrado por otro usuario.", "error")
            return render_template('editar_perfil.html', 
                usuario=usuario, email=user_data['email'],
                telefono=user_data.get('telefono', ''), direccion=user_data.get('direccion', ''))

        try:
            collection.update_one({'usuario': usuario}, {
                '$set': {'email': email, 'telefono': telefono, 'direccion': direccion}
            })
            flash("¡Perfil actualizado con éxito!", "success")
            return redirect(url_for('mi_perfil'))
        except Exception as e:
            print(f"Error al actualizar perfil: {e}")
            flash("Error al actualizar el perfil. Inténtalo nuevamente.", "error")

    return render_template('editar_perfil.html', 
        usuario=usuario, email=user_data['email'],
        telefono=user_data.get('telefono', ''), direccion=user_data.get('direccion', ''))

@app.route('/cambiar_contrasena', methods=['GET', 'POST'])
def cambiar_contrasena():
    if 'usuario' not in session:
        flash("Debes iniciar sesión para cambiar tu contraseña", "error")
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    if request.method == 'POST':
        actual = request.form['contrasena_actual']
        nueva = request.form['nueva_contrasena']
        confirmar = request.form['confirmar_contrasena']
        user = collection.find_one({'usuario': usuario})

        if not bcrypt.check_password_hash(user['contrasena'], actual):
            flash("La contraseña actual es incorrecta.", "error")
            return render_template('cambiar_contrasena.html', usuario=usuario)

        if nueva != confirmar:
            flash("Las nuevas contraseñas no coinciden.", "error")
            return render_template('cambiar_contrasena.html', usuario=usuario)

        hashed = bcrypt.generate_password_hash(nueva).decode('utf-8')
        collection.update_one({'usuario': usuario}, {'$set': {'contrasena': hashed}})
        flash("¡Contraseña actualizada con éxito!", "success")
        return redirect(url_for('mi_perfil'))

    return render_template('cambiar_contrasena.html', usuario=usuario)


@app.route('/agregar_servicio', methods=['GET', 'POST'])
def agregar_servicio():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio')
        icono = request.form.get('icono')
        categoria = request.form.get('categoria')
        
        # Procesar la imagen
        if 'imagen' in request.files:
            archivo = request.files['imagen']
            if archivo and allowed_file(archivo.filename):
                # Generar un nombre seguro para el archivo
                filename = secure_filename(archivo.filename)
                # Añadir un timestamp para evitar nombres duplicados
                import time
                timestamp = str(int(time.time()))
                nombre_archivo = f"{timestamp}_{filename}"
                
                # Crear el directorio si no existe
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                
                # Guardar el archivo en la carpeta img
                archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo))
                
                # Guardar en la base de datos
                nuevo_servicio = {
                    'nombre': nombre,
                    'descripcion': descripcion,
                    'precio': float(precio),
                    'icono': icono,
                    'imagen': nombre_archivo,  # Guarda solo el nombre del archivo
                    'categoria': categoria
                }
                
                # Insertar en la base de datos (ajusta según tu implementación)
                db.servicios.insert_one(nuevo_servicio)
                
                flash('Servicio agregado correctamente', 'success')
                return redirect(url_for('servicios'))
            else:
                flash('Formato de archivo no permitido', 'danger')
        else:
            flash('Se requiere una imagen para el servicio', 'danger')
    
    # Para el método GET, renderiza la plantilla
    return render_template('agregar_servicio.html', usuario=session.get('usuario'), tipo_usuario=session.get('tipo_usuario'))
@app.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        usuario = collection.find_one({'email': email})
        if usuario:
            token = serializer.dumps(email, salt='password-reset-salt')
            enlace = url_for('restablecer_contrasena', token=token, _external=True)
            asunto = "Recuperación de contraseña - FastHelp"
            cuerpo = f"""<p>Hola {usuario['usuario']}, hemos recibido una solicitud para restablecer tu contraseña.</p>
            <p>Haz clic en el siguiente enlace:</p><a href="{enlace}">Restablecer contraseña</a>"""
            enviar_email(email, asunto, cuerpo)
            flash("Correo de recuperación enviado.", "success")
        else:
            flash("El correo electrónico no está registrado.", "error")

    return render_template('recuperar_contrasena.html')

@app.route('/restablecer_contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash("El enlace ha caducado o es inválido.", "error")
        return redirect(url_for('recuperar_contrasena'))

    if request.method == 'POST':
        nueva = request.form['nueva_contrasena']
        confirmar = request.form['confirmar_contrasena']
        if nueva != confirmar:
            flash("Las contraseñas no coinciden.", "error")
        else:
            hashed = bcrypt.generate_password_hash(nueva).decode('utf-8')
            collection.update_one({'email': email}, {'$set': {'contrasena': hashed}})
            flash("Contraseña restablecida con éxito.", "success")
            return redirect(url_for('login'))

    return render_template('restablecer_contrasena.html')

@app.route('/nomina')
def nomina():
    # Asegurarse de que el usuario tenga el rol de 'jefe'
    if 'usuario' not in session or session.get('tipo_usuario') != 'jefe':
        flash("Acceso denegado. Solo el jefe puede ver la nómina.", "error")
        return redirect(url_for('index'))

    # Obtener todos los empleados desde la base de datos
    empleados = list(collection.find({'tipo_usuario': 'empleado'}))
    
    # Verificar si hay empleados
    if not empleados:
        flash("No hay empleados registrados.", "warning")
    
    # Aquí podrías añadir lógica adicional para calcular los pagos, como horas extras, etc.
    for empleado in empleados:
        # Ejemplo de cálculo: agregar un campo de 'pago_total' al empleado
        horas_extra = empleado.get('horas_extra', 0)  # Supón que tenemos horas extra
        salario_base = empleado.get('salario_base', 1000)  # Ejemplo de salario base
        pago_extra = horas_extra * 20  # Supón que cada hora extra se paga 20
        pago_total = salario_base + pago_extra
        empleado['pago_total'] = pago_total

    return render_template('nomina.html', empleados=empleados)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('tipo_usuario', None)
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for('login'))

# Rutas estáticas
@app.route('/mi_carrito')
def mi_carrito():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('mi_carrito.html', usuario=session['usuario'])

@app.route('/acerca_de')
def acerca_de():
    return render_template('acerca_de.html')

@app.route('/servicios')
def servicios():
    # Obtener todos los servicios de la base de datos
    servicios_lista = list(db.servicios.find())
    
    # Renderizar la plantilla con los servicios
    return render_template('servicios.html', 
                          servicios=servicios_lista, 
                          usuario=session.get('usuario'), 
                          tipo_usuario=session.get('tipo_usuario'))

@app.route('/eliminar_servicio/<servicio_id>', methods=['POST'])
def eliminar_servicio(servicio_id):
    # Verificar que el usuario sea jefe
    if 'usuario' not in session or session.get('tipo_usuario') != 'jefe':
        flash("Acceso denegado. Solo el jefe puede eliminar servicios.", "error")
        return redirect(url_for('servicios'))
    
    try:
        from bson.objectid import ObjectId
        # Eliminar el servicio de la base de datos
        servicios_collection = db['servicios']
        result = servicios_collection.delete_one({'_id': ObjectId(servicio_id)})
        
        if result.deleted_count == 1:
            flash("Servicio eliminado exitosamente.", "success")
        else:
            flash("No se pudo eliminar el servicio.", "error")
    except Exception as e:
        flash(f"Error al eliminar el servicio: {str(e)}", "error")
    
    return redirect(url_for('servicios'))

@app.route('/profesionales')
def profesionales():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('profesionales.html', usuario=session['usuario'])

@app.route('/como_funciona')
def como_funciona():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('como_funciona.html', usuario=session['usuario'])

@app.route('/mis_servicios')
def mis_servicios():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('mis_servicios.html', usuario=session['usuario'])

@app.route('/solicitar_servicio')
def solicitar_servicio():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('solicitar_servicio.html', usuario=session['usuario'])

@app.route('/servicio/<categoria>')
def servicio_especifico(categoria):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('servicios.html', usuario=session['usuario'], categoria_seleccionada=categoria)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)