"""
🎤 SPEECH RECOGNITION TEST

This script tests if Windows Speech Recognition works on your PC.
Just run it and speak when prompted!
"""

import subprocess
import sys

print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   🎤 SPEECH RECOGNITION TEST                                          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")

print("  Step 1: Checking if Windows Speech API is available...")

# Test if System.Speech is available
test_cmd = 'Add-Type -AssemblyName System.Speech; Write-Output "SPEECH_OK"'
result = subprocess.run(['powershell', '-Command', test_cmd], capture_output=True, text=True)

if 'SPEECH_OK' not in result.stdout:
    print("  ❌ Windows Speech API not available!")
    print(f"     Error: {result.stderr}")
    sys.exit(1)

print("  ✅ Windows Speech API is available!")
print()
print("  Step 2: Testing microphone and speech recognition...")
print()
print("  ╔════════════════════════════════════════════════════════════╗")
print("  ║  🔴 SPEAK NOW! Say something like 'Hello' or 'Test'        ║")
print("  ║     You have 10 seconds...                                 ║")
print("  ╚════════════════════════════════════════════════════════════╝")
print()

# PowerShell script for speech recognition
speech_script = '''
Add-Type -AssemblyName System.Speech

$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()

# Load dictation grammar
$grammar = New-Object System.Speech.Recognition.DictationGrammar
$recognizer.LoadGrammar($grammar)

# Set timeouts
$recognizer.InitialSilenceTimeout = [TimeSpan]::FromSeconds(10)
$recognizer.EndSilenceTimeout = [TimeSpan]::FromSeconds(2)
$recognizer.BabbleTimeout = [TimeSpan]::FromSeconds(10)

try {
    $result = $recognizer.Recognize()
    if ($result -and $result.Text) {
        Write-Output "RECOGNIZED:$($result.Text)"
        Write-Output "CONFIDENCE:$($result.Confidence)"
    } else {
        Write-Output "NO_SPEECH_DETECTED"
    }
} catch {
    Write-Output "ERROR:$($_.Exception.Message)"
} finally {
    $recognizer.Dispose()
}
'''

try:
    result = subprocess.run(
        ['powershell', '-Command', speech_script],
        capture_output=True,
        text=True,
        timeout=20
    )
    
    output = result.stdout.strip()
    
    if 'RECOGNIZED:' in output:
        lines = output.split('\n')
        for line in lines:
            if line.startswith('RECOGNIZED:'):
                text = line.replace('RECOGNIZED:', '')
                print(f"  ✅ SUCCESS! I heard: \"{text}\"")
            if line.startswith('CONFIDENCE:'):
                conf = float(line.replace('CONFIDENCE:', ''))
                print(f"     Confidence: {conf*100:.0f}%")
        print()
        print("  🎉 Speech recognition is WORKING!")
        print()
        print("  You can now run the assistant:")
        print("     python assistant_windows.py")
        print()
        print("  TIP: When you see the prompt, just press ENTER (empty)")
        print("       to activate voice mode, then speak your command.")
        
    elif 'NO_SPEECH_DETECTED' in output:
        print("  ⚠️  No speech was detected!")
        print()
        print("  Possible reasons:")
        print("    1. Microphone is muted or not connected")
        print("    2. Microphone volume is too low")
        print("    3. You didn't speak loud enough")
        print("    4. Background noise is too high")
        print()
        print("  Try these fixes:")
        print("    - Check Windows Sound Settings → Input → Microphone")
        print("    - Speak louder and closer to the microphone")
        print("    - Run this test again")
        
    elif 'ERROR:' in output:
        error_msg = output.replace('ERROR:', '')
        print(f"  ❌ Error: {error_msg}")
        print()
        print("  This might mean:")
        print("    - No microphone is connected")
        print("    - Microphone permissions are blocked")
        print("    - Another app is using the microphone")
        
    else:
        print(f"  ❓ Unexpected result: {output}")
        if result.stderr:
            print(f"     Stderr: {result.stderr}")

except subprocess.TimeoutExpired:
    print("  ⏰ Timeout - no speech detected in 20 seconds")
    print()
    print("  Make sure your microphone is working and try again.")

except Exception as e:
    print(f"  ❌ Error: {e}")

print()
input("  Press ENTER to exit...")
