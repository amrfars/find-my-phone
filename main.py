import os
import threading
import time

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.utils import platform

# Android-specific imports
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android import mActivity
    from jnius import autoclass

    PythonService = autoclass('org.kivy.android.PythonService')
    Context = autoclass('android.content.Context')
    AudioManager = autoclass('android.media.AudioManager')

WAKE_WORD = "يا عمرو"


class FindMyPhoneApp(App):
    def build(self):
        self.listening = False
        self.service_running = False

        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)

        title = Label(
            text="🔍 اعثر على هاتفك",
            font_size='28sp',
            size_hint_y=0.2,
            color=(0.95, 0.69, 0.1, 1)
        )

        self.status_label = Label(
            text="الخدمة متوقفة",
            font_size='18sp',
            size_hint_y=0.15,
            color=(0.8, 0.8, 0.8, 1)
        )

        self.toggle_btn = ToggleButton(
            text="▶ تشغيل الاستماع",
            font_size='20sp',
            size_hint_y=0.2,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        self.toggle_btn.bind(on_press=self.toggle_listening)

        info = Label(
            text='قول "يا عمرو" وهاتفك هييرن ويشتغل الفلاش\n\n'
                 'الخدمة بتشتغل في الخلفية عشان تسمعك دايماً',
            font_size='14sp',
            size_hint_y=0.3,
            color=(0.6, 0.6, 0.6, 1),
            halign='center'
        )

        layout.add_widget(title)
        layout.add_widget(self.status_label)
        layout.add_widget(self.toggle_btn)
        layout.add_widget(info)

        # Request permissions on start
        if platform == 'android':
            Clock.schedule_once(self.request_perms, 1)

        return layout

    def request_perms(self, dt):
        request_permissions([
            Permission.RECORD_AUDIO,
            Permission.CAMERA,
            Permission.FOREGROUND_SERVICE,
            Permission.POST_NOTIFICATIONS,
            Permission.VIBRATE,
            Permission.WRITE_SETTINGS,
            Permission.READ_EXTERNAL_STORAGE,
        ])

    def toggle_listening(self, instance):
        if self.listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self):
        self.listening = True
        self.toggle_btn.text = "⏹ إيقاف الاستماع"
        self.toggle_btn.background_color = (0.8, 0.2, 0.2, 1)
        self.status_label.text = "🟢 يستمع دلوقتي..."
        self.status_label.color = (0.3, 0.9, 0.3, 1)

        if platform == 'android':
            self.start_foreground_service()
        else:
            # Desktop: run listener in thread for testing
            threading.Thread(target=self.listen_loop, daemon=True).start()

    def stop_listening(self):
        self.listening = False
        self.toggle_btn.text = "▶ تشغيل الاستماع"
        self.toggle_btn.background_color = (0.2, 0.6, 0.2, 1)
        self.status_label.text = "الخدمة متوقفة"
        self.status_label.color = (0.8, 0.8, 0.8, 1)

        if platform == 'android' and self.service_running:
            self.stop_foreground_service()

    def start_foreground_service(self):
        if platform != 'android':
            return
        try:
            service_args = os.path.join(os.path.dirname(__file__), 'service.py')
            PythonService.start(
                'Find My Phone - Listening',
                service_args,
                'listen_service',
                True
            )
            self.service_running = True
        except Exception as e:
            self.status_label.text = f"خطأ: {e}"

    def stop_foreground_service(self):
        if platform != 'android':
            return
        try:
            PythonService.stop('listen_service')
            self.service_running = False
        except Exception as e:
            self.status_label.text = f"خطأ: {e}"

    def listen_loop(self):
        """Desktop fallback: simple listen loop using speech_recognition."""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            mic = sr.Microphone()

            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=2)

            while self.listening:
                try:
                    with mic as source:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    text = recognizer.recognize_google(audio, language="ar-EG")
                    Clock.schedule_once(lambda dt: self.status_label.text.setter(f"سمعت: {text}"))
                    if WAKE_WORD in text:
                        self.trigger_alert()
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception:
                    pass
        except ImportError:
            Clock.schedule_once(lambda dt: self.status_label.text.setter("ثبّت speech_recognition أولاً"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.status_label.text.setter(f"خطأ: {e}"))

    def trigger_alert(self):
        """Max volume + torch + alarm sound."""
        if platform == 'android':
            self.android_alert()
        else:
            # Desktop fallback
            self.status_label.text = "🔔 🔦 ياعمرو! هاتفك هنا!"
            self.status_label.color = (1, 0.2, 0.2, 1)
            try:
                import winsound
                for _ in range(10):
                    winsound.Beep(2000, 300)
            except Exception:
                pass

    def android_alert(self):
        try:
            # Max volume
            am = mActivity.getSystemService(Context.AUDIO_SERVICE)
            max_vol = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
            am.setStreamVolume(AudioManager.STREAM_MUSIC, max_vol, 0)

            # Torch ON
            try:
                CameraManager = autoclass('android.hardware.camera2.CameraManager')
                cm = mActivity.getSystemService(Context.CAMERA_SERVICE)
                cam_ids = cm.getCameraIdList()
                for cid in cam_ids:
                    cm.setTorchMode(cid, True)
            except Exception:
                pass

            # Play alarm
            alarm_path = os.path.join(os.path.dirname(__file__), 'alarm.mp3')
            if os.path.exists(alarm_path):
                sound = SoundLoader.load(alarm_path)
                if sound:
                    sound.play()

            # Vibrate
            try:
                Vibrator = autoclass('android.os.Vibrator')
                v = mActivity.getSystemService(Context.VIBRATOR_SERVICE)
                if v:
                    v.vibrate(2000)
            except Exception:
                pass

            # Turn off torch after 10 seconds
            threading.Timer(10, self.turn_off_torch).start()

        except Exception as e:
            self.status_label.text = f"خطأ في التنبيه: {e}"

    def turn_off_torch(self):
        try:
            CameraManager = autoclass('android.hardware.camera2.CameraManager')
            cm = mActivity.getSystemService(Context.CAMERA_SERVICE)
            cam_ids = cm.getCameraIdList()
            for cid in cam_ids:
                cm.setTorchMode(cid, False)
        except Exception:
            pass


if __name__ == '__main__':
    FindMyPhoneApp().run()
