# 🚀 Trading Robot Setup - Easy Guide for Beginners!

## 👋 Hello! Welcome to Your Trading Robot!

This is like having a smart robot that can help you buy and sell things on the internet money market. But first, we need to set it up together!

## 📦 What You Need Before We Start

### 1. **Computer Stuff You Need:**
- A computer (like the one you're using now!)
- Something called "Docker" - it's like a magic box that makes programs work
- A program called "Git" - it's like a copy machine for computer files

### 2. **Internet Money Accounts:**
You need special accounts where the robot can buy and sell:
- **Coinbase account** - like a bank for internet money
- **Binance account** - another bank for internet money
- **Kraken account** - one more bank for internet money

## 🛠️ Step 1: Get the Robot Files

First, we need to get all the robot's parts. It's like getting all the pieces for a puzzle!

**Open your computer and type this:**
```bash
git clone https://github.com/yourname/trading-bot.git
cd trading-bot
```

This is like saying "please copy all the robot pieces to my computer!"

## 🐳 Step 2: Set Up the Magic Box (Docker)

Docker is like a magic box that makes our robot work. We need to make sure it's ready!

**Type this to check if Docker is working:**
```bash
docker --version
```

If it shows a version number, great! If not, you need to install Docker first.

## 🔑 Step 3: Tell the Robot Your Secret Codes

The robot needs special codes to talk to the money banks. These are like secret passwords!

**Open the `.env` file and change these lines:**

```bash
# Change these to your real codes:
BINANCE_API_KEY=your_real_binance_key_here
BINANCE_API_SECRET=your_real_binance_secret_here

KRAKEN_API_KEY=your_real_kraken_key_here
KRAKEN_API_SECRET=your_real_kraken_secret_here

COINBASE_API_KEY_NAME=your_real_coinbase_key_here
COINBASE_API_PRIVATE_KEY=your_real_coinbase_secret_here
```

**⚠️ SUPER IMPORTANT:** Never share these secret codes with anyone! They're like your house keys!

## 🎮 Step 4: Make the Robot Wake Up!

Now we tell the robot to start working!

**Type this to start the robot:**
```bash
docker-compose up -d trading-bot
```

This is like saying "Robot, wake up and start working!"

## 👀 Step 5: Check if the Robot is Happy

Let's make sure our robot is working and feeling good!

**Check if the robot is running:**
```bash
docker ps
```

You should see something like:
```
kraken-trading-bot   Up 2 minutes   0.0.0.0:8080->8080/tcp
```

**Ask the robot how it's feeling:**
```bash
curl http://localhost:8080/health
```

If it says `"status": "healthy"`, then the robot is happy! 🎉

## 🎨 Step 6: Look at the Robot's Face (Web Page)

The robot has a pretty web page where you can see what it's doing!

**Open your web browser and go to:**
```
http://localhost:8080/health
```

You can also see:
- **Logs**: http://localhost:8080/logs (what the robot has been doing)
- **Portfolio**: http://localhost:8080/portfolio (what money the robot has)

## 🎯 Step 7: Test the Robot (Safely!)

Before we let the robot play with real money, let's test it with pretend money!

**Change this in your `.env` file:**
```bash
TEST_MODE=true
```

**Restart the robot:**
```bash
docker-compose restart trading-bot
```

Now the robot will practice with pretend money! It's like playing with toy money.

## 💰 Step 8: Let the Robot Play with Real Money

When you're ready for the robot to use real money:

**Change this back in your `.env` file:**
```bash
TEST_MODE=false
```

**Restart the robot:**
```bash
docker-compose restart trading-bot
```

**⚠️ BIG WARNING:** Now the robot will buy and sell with REAL MONEY! Be very careful!

## 🛑 Step 9: Tell the Robot to Take a Nap

When you want the robot to stop working:

```bash
docker-compose down
```

This is like saying "Robot, go to sleep!"

## 🔧 Robot Care Instructions

### How to Check if Robot is Still Working:
```bash
docker ps -f name=kraken-trading-bot
```

### How to See What Robot Did Today:
```bash
docker logs kraken-trading-bot
```

### How to Wake Up Robot Again:
```bash
docker-compose up -d trading-bot
```

## 🚨 If Something Goes Wrong

### Robot Won't Start:
1. Make sure Docker is running
2. Check your secret codes in `.env` file
3. Try: `docker-compose down` then `docker-compose up -d trading-bot`

### Can't See Web Page:
1. Make sure robot is running: `docker ps`
2. Check: http://localhost:8080/health
3. Wait a few seconds and try again

### Robot is Sad (Errors):
```bash
docker logs kraken-trading-bot --tail 20
```
This will show you what the robot is thinking about.

## 🎉 You're Done!

Congratulations! You now have your own trading robot! 🎊

**Remember:**
- Always start with `TEST_MODE=true` to practice
- Never share your secret codes
- Check on your robot every day
- Start with small amounts of money
- Have fun learning about trading! 🚀

## 📚 Words You Might Hear

- **API Key**: Like a secret password for the robot to talk to banks
- **Docker**: Magic box that makes programs work
- **Container**: Like a little house where the robot lives
- **Test Mode**: Practice with pretend money
- **Production**: Using real money
- **Logs**: Stories about what the robot did
- **Portfolio**: List of what the robot owns

---

**Made with ❤️ for beginners!** If you get stuck, ask a grown-up who knows about computers!