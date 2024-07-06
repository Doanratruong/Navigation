#!/usr/bin/env python
import rospy
import subprocess

def capture_audio(timeout_sec=10):
    rospy.loginfo("Listening...")

    try:
        process = subprocess.Popen(["arecord", "-f", "cd", "-t", "raw"], stdout=subprocess.PIPE)
        audio_data, _ = process.communicate(timeout=timeout_sec)
        rospy.loginfo("Stop listening.")

        if audio_data:
            rospy.loginfo(f"Captured audio: {audio_data}")
            return audio_data
        else:
            rospy.logwarn("No audio data captured.")
            return None
    except subprocess.TimeoutExpired:
        rospy.logwarn("Audio capture timed out.")
        process.kill()  # Kill the process if timeout occurs
        return None

def process_audio(audio_data):
    if audio_data is not None:
        if b"start" in audio_data.lower():  # Adjust condition based on actual audio processing
            return True
    return False

def microphone_listener():
    rospy.init_node('microphone_listener', anonymous=True)

    while not rospy.is_shutdown():
        audio_data = capture_audio()
        if audio_data is not None:
            if process_audio(audio_data):
                # Perform goal setting or other actions here
                rospy.loginfo("Setting goal...")
        rospy.sleep(1.0)  # Adjust sleep duration as needed

if __name__ == '__main__':
    try:
        microphone_listener()
    except rospy.ROSInterruptException:
        pass

