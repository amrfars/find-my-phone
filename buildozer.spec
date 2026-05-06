[app]

# (str) Title of your application
title = اعثر على هاتفك - يا عمرو

# (str) Package name
package.name = findmyphone

# (str) Package domain
package.domain = org.amrfa

# (str) Source code directory
source.dir = .

# (str) Application version
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy==2.3.0,speechrecognition,pyjnius,pyaudio

# (str) Presplash image
presplash.filename = %(source.dir)s/presplash.png

# (str) Icon
icon.filename = %(source.dir)s/icon.png

# (str) Supported orientation
orientation = portrait

# (bool) Fullscreen
fullscreen = 1

# (list) Android permissions
android.permissions = RECORD_AUDIO,CAMERA,VIBRATE,WRITE_SETTINGS,FOREGROUND_SERVICE,POST_NOTIFICATIONS,WAKE_LOCK

# (str) Android service entry point
services = listen_service:service.py:foreground

# (bool) Stay awake
android.wakelock = True

# (bool) Accept Android SDK license automatically
android.accept_sdk_license = True

# (str) Android API level
android.api = 33

# (str) Android arch
android.archs = arm64-v8a, armeabi-v7a

# (bool) Copy lib
android.copy_libs = 1

# (str) Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# (str) Logcat filter
android.logcat_filters = *:S python:D

# (str) Android allow backup
android.allow_backup = True

# (list) Android gradle dependencies
android.gradle_dependencies = com.google.android.material:material:1.6.0
