import speech_recognition as sr
import pyttsx3
import requests
import time

API = "http://127.0.0.1:8000"

engine = pyttsx3.init()
engine.setProperty('rate', 175)

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True


def speak(text):
    print(f"Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()


def listen():
    with sr.Microphone() as source:
        print("Sun raha hoon... (bolo ab)")
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=5)
            print("Samajh raha hoon...")
            text = recognizer.recognize_google(audio, language="en-IN")
            print(f"Aap: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"Error: {e}")
            return ""


def get_crypto(symbol):
    try:
        r = requests.get(f"{API}/api/crypto/{symbol}", timeout=5)
        data = r.json()
        if "price" in data:
            return data["price"], data.get("change_24h", 0)
    except Exception:
        pass
    return None, None


def get_all_data():
    try:
        r = requests.get(f"{API}/api/all", timeout=10)
        return r.json()
    except Exception:
        return None


def get_forex(symbol_part):
    data = get_all_data()
    if not data:
        return None
    for item in data.get("forex_gold", []):
        if symbol_part.lower() in item.get("symbol", "").lower():
            return item
    return None


def handle_command(cmd):
    if not cmd:
        return False

    if any(w in cmd for w in ["exit", "quit", "bye", "band", "stop"]):
        speak("Theek hai, band kar raha hoon. Khuda hafiz!")
        return True

    if "bitcoin" in cmd or "btc" in cmd:
        price, chg = get_crypto("btc")
        if price:
            direction = "upar" if chg >= 0 else "neeche"
            speak(f"Bitcoin abhi {price:.0f} dollars pe hai. 24 ghante mein {abs(chg):.2f} percent {direction}.")
        else:
            speak("Bitcoin ka data nahi mil raha.")
        return False

    if "ethereum" in cmd or "eth" in cmd:
        price, chg = get_crypto("eth")
        if price:
            direction = "upar" if chg >= 0 else "neeche"
            speak(f"Ethereum abhi {price:.0f} dollars pe hai. {abs(chg):.2f} percent {direction}.")
        else:
            speak("Ethereum ka data nahi mil raha.")
        return False

    if "solana" in cmd or "sol" in cmd:
        price, chg = get_crypto("sol")
        if price:
            speak(f"Solana abhi {price:.2f} dollars pe hai.")
        return False

    if "gold" in cmd or "sona" in cmd or "xau" in cmd:
        item = get_forex("XAU")
        if item and item.get("price"):
            speak(f"Gold abhi {item['price']:.2f} dollars per ounce hai.")
        else:
            speak("Gold ka data nahi mil raha.")
        return False

    if "euro" in cmd or "eur" in cmd:
        item = get_forex("EUR")
        if item and item.get("price"):
            speak(f"Euro dollar ke against {item['price']:.4f} pe hai.")
        else:
            speak("Euro ka data nahi mil raha.")
        return False

    if "pound" in cmd or "gbp" in cmd:
        item = get_forex("GBP")
        if item and item.get("price"):
            speak(f"British pound {item['price']:.4f} pe hai.")
        return False

    if "yen" in cmd or "jpy" in cmd:
        item = get_forex("JPY")
        if item and item.get("price"):
            speak(f"Dollar yen ke against {item['price']:.2f} pe hai.")
        return False

    if "market" in cmd or "sab" in cmd or "all" in cmd or "summary" in cmd:
        data = get_all_data()
        if data:
            btc = next((c for c in data["crypto"] if c["name"] == "BTC"), None)
            gold = next((f for f in data["forex_gold"] if f["symbol"] == "XAU/USD"), None)
            msg = "Market update: "
            if btc:
                msg += f"Bitcoin {btc['price']:.0f} dollars. "
            if gold and gold.get("price"):
                msg += f"Gold {gold['price']:.0f} dollars."
            speak(msg)
        return False

    if "help" in cmd or "kya kar" in cmd or "madad" in cmd:
        speak("Aap pooch sakte ho: Bitcoin ka price, Ethereum ka price, Gold ka rate, ya market summary.")
        return False

    speak("Maaf kijiye, samajh nahi aaya. Bitcoin, Ethereum, Gold, ya market summary poochiye.")
    return False


def main():
    print("=" * 50)
    print("       JARVIS VOICE ASSISTANT")
    print("=" * 50)
    print("Commands jo aap bol sakte ho:")
    print("  - Bitcoin ka price kya hai?")
    print("  - Ethereum kitne ka hai?")
    print("  - Gold ka rate batao")
    print("  - Market summary")
    print("  - Bye (band karne ke liye)")
    print("=" * 50)

    speak("Jarvis tayyar hai. Boliye kya jaanna hai?")

    while True:
        try:
            cmd = listen()
            if cmd:
                should_exit = handle_command(cmd)
                if should_exit:
                    break
            time.sleep(0.3)
        except KeyboardInterrupt:
            print("\nBye!")
            break


if __name__ == "__main__":
    main()