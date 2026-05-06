"""
Background service for continuous wake-word listening on Android.
This runs as a foreground service so it stays alive even when the app is minimized.
"""
import os
import time
import threading

WAKE_WORD = "يا عمرو"


def run():
    """Main service loop - listens for wake word and triggers alert."""
    try:
        import speech_recognition as sr
        from jnius import autoclass

        Context = autoclass('android.content.Context')
        AudioManager = autoclass('android.media.AudioManager')
        mActivity = autoclass('org.kivy.android.PythonActivity').mActivity

        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        # Adjust for ambient noise
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=2)

        print("[FindMyPhone] Service started, listening...")

        while True:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=8, phrase_time_limit=5)

                try:
                    text = recognizer.recognize_google(audio, language="ar-EG")
                    print(f"[FindMyPhone] Heard: {text}")

                    if WAKE_WORD in text:
                        print("[FindMyPhone] Wake word detected! Triggering alert...")
                        trigger_android_alert(mActivity)
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    print(f"[FindMyPhone] Recognition error: {e}")

            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                print(f"[FindMyPhone] Listen error: {e}")
                time.sleep(1)

    except Exception as e:
        print(f"[FindMyPhone] Service error: {e}")


def trigger_android_alert(mActivity):
    """Max volume + torch + vibration + alarm sound."""
    try:
        from jnius import autoclass
        from kivy.core.audio import SoundLoader

        Context = autoclass('android.content.Context')
        AudioManager = autoclass('android.media.AudioManager')

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
        except Exception as e:
            print(f"[FindMyPhone] Torch error: {e}")

        # Vibrate
        try:
            Vibrator = autoclass('android.os.Vibrator')
            v = mActivity.getSystemService(Context.VIBRATOR_SERVICE)
            if v:
                v.vibrate(2000)
        except Exception as e:
            print(f"[FindMyPhone] Vibrate error: {e}")

        # Play alarm
        alarm_path = os.path.join(os.path.dirname(__file__), 'alarm.mp3')
        if os.path.exists(alarm_path):
            sound = SoundLoader.load(alarm_path)
            if sound:
                sound.play()

        # Turn off torch after 10 seconds
        threading.Timer(10, lambda: turn_off_torch(mActivity)).start()

    except Exception as e:
        print(f"[FindMyPhone] Alert error: {e}")


def turn_off_torch(mActivity):
    try:
        CameraManager = autoclass('android.hardware.camera2.CameraManager')
        cm = mActivity.getSystemService(Context.CAMERA_SERVICE)
        cam_ids = cm.getCameraIdList()
        for cid in cam_ids:
            cm.setTorchMode(cid, False)
    except Exception:
        pass


if __name__ == '__main__':
    run()
