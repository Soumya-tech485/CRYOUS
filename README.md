# Author

## Soumya Ranjan Moharana

**Founder & Creator of CRYOUS**

I'm a Computer Science student and AI developer from India, passionate about building intelligent systems that go beyond traditional chatbots.

CRYOUS began as a personal vision to create a truly voice-first, self-improving AI operating system capable of understanding, reasoning, learning, and assisting with everyday computing tasks. The long-term goal is to develop an open, modular AI platform that combines local intelligence, cloud models, autonomous agents, and seamless human-computer interaction.

My primary interests include:

* Artificial Intelligence & Machine Learning
* Large Language Models (LLMs)
* Multi-Agent AI Systems
* AI Automation
* Human-AI Interaction
* Open-Source Software
* Intelligent Operating Systems

---

### Connect

* GitHub: https://github.com/Soumya-tech485
* LinkedIn: https://www.linkedin.com/in/soumya-ranjan-moharana-61495a40a/
* Email: soumyarm123121@gmail.com

If you find CRYOUS useful, consider giving the repository a star. Every contribution, suggestion, bug report, or feature request helps make the project better.

#  CRYOUS v1.0

> **A self-growing, voice-first AI operating system built for developers, researchers, and power users.**
>
> **Local-first. Multi-agent. Privacy-focused. Designed to evolve with you.**



# Overview

CRYOUS is not just another AI assistant.

It is a modular AI operating system that combines local intelligence, cloud AI models, autonomous agents, voice interaction, memory, and self-learning into a single platform.

Instead of acting like a chatbot, CRYOUS behaves like a personal AI operator that can listen, think, plan, execute tasks, learn new skills, and continuously improve over time.

The project is designed with a **local-first philosophy**, meaning your computer handles as much work as possible while intelligently using free cloud models only when necessary.



# Core Philosophy

CRYOUS is built around five principles:

* **Voice First** — interact naturally without opening applications or typing commands.
* **Local First** — maximize privacy and minimize cloud dependency.
* **Self Growing** — continuously learn new skills and improve through experience.
* **Modular by Design** — every capability exists as an independent agent or plugin.
* **Efficient AI Routing** — automatically choose the best model for every task.



# Features

##  Natural Voice Assistant

Wake CRYOUS simply by saying:

> **"Cryous"**

It immediately becomes active and responds naturally:

> *"Yes boss, what can I do for you?"*

After completing your request, it asks whether you need anything else before returning to standby mode.

Voice interaction is designed to feel conversational rather than robotic.



##  Local-First Architecture

When idle, CRYOUS keeps only the wake-word engine active.

This provides:

* Extremely low CPU usage
* Zero unnecessary API requests
* Fast wake-up time
* Better privacy

Heavy workloads only run when needed.

---

##  Multi-Agent Intelligence

Instead of relying on one giant AI model, CRYOUS distributes work among specialized agents.

Examples include:

* Research Agent
* Planning Agent
* Coding Agent
* Memory Agent
* Browser Agent
* File Agent
* Device Control Agent
* Report Generator
* Plugin Manager

Each agent focuses on a specific responsibility while the core orchestrator coordinates them.

---

##  Smart AI Routing

CRYOUS intelligently decides which AI model should answer each request.

For example:

* Greetings → Local response
* Simple questions → Lightweight models
* Coding → High-performance coding models
* Research → Larger reasoning models
* Long analysis → Best available reasoning provider

This dramatically reduces API usage while maintaining response quality.

---

##  Token Optimization

Every API token matters.

CRYOUS includes several optimization techniques:

* Intelligent model routing
* Response caching
* Conversation compression
* Duplicate request detection
* Automatic provider failover
* Weekly token budgeting
* Usage monitoring

The result is significantly lower API costs without sacrificing performance.

---

##  Persistent Memory

CRYOUS remembers useful information over time.

It can remember:

* User preferences
* Frequently used commands
* Learned shortcuts
* Custom workflows
* Previous conversations
* Personalized skills

Memory becomes more useful as you continue using the system.



##  Self-Learning

One of the defining features of CRYOUS is its ability to learn.

Example:

> **"Cryous, learn: when I say deployment checklist, open release notes."**

From that point forward, CRYOUS understands the shortcut and executes it automatically.

No programming required.



##  Plugin Generation

CRYOUS can generate entirely new capabilities using natural language.

Example:

> **"Cryous, create a weather plugin using Open-Meteo."**

The system can:

* generate the plugin
* validate the code
* install dependencies
* register the plugin
* hot-load it without restarting

The goal is to allow the assistant to expand its own capabilities over time.



##  Multiple AI Providers

CRYOUS supports multiple AI providers simultaneously.

Supported providers include:

* Google Gemini
* Groq
* OpenRouter
* Ollama (Local Models)

The routing engine automatically switches providers based on availability, latency, and workload.



##  Dashboard

The built-in dashboard provides a live view of the system.

Features include:

* Running agents
* AI provider status
* Token usage
* Memory statistics
* Logs
* Active tasks
* Performance metrics
* Plugin management

Everything is accessible through a simple web interface.



##  Privacy

Privacy is a core design goal.

CRYOUS:

* Executes local commands without cloud access
* Minimizes external API usage
* Stores memories locally
* Uses encrypted configuration files where applicable
* Allows complete offline operation when using local models

Your data remains under your control.



# Installation

Getting started takes only a few minutes.

### 1. Clone the repository

```bash
git clone https://github.com/Soumya-tech485/CRYOUS.git
cd cryous
```

---

### 2. Run the installer

```bash
install.bat
```

---

### 3. Configure API keys

Copy:

```text
.env.example
```

to

```text
.env
```

Then add at least one provider.

Recommended:

* Gemini (largest free quota)
* Groq (fastest inference)
* OpenRouter (wide range of free models)

---

### 4. Start CRYOUS

```bash
run.bat
```

Open:

```
http://127.0.0.1:8123
```

---

### 5. Optional Windows Startup

Automatically launch CRYOUS when Windows starts.

```bash
python scripts/autostart.py
```

---

# Voice Workflow

When your PC starts:

```
Standby
     │
     ▼
Say "Cryous"
     │
     ▼
"Yes boss, what can I do for you?"
     │
     ▼
Execute request
     │
     ▼
Short spoken summary
     │
     ▼
"Anything else?"
     │
     ▼
No
     │
     ▼
Return to standby
```

The assistant remains lightweight while waiting for activation.

---

# Performance

Optimized for modern laptops, including the Dell G15.

Typical idle usage:

* CPU: ~1–3%
* Network: None
* Memory: Minimal
* Wake latency: Near-instant

Heavy tasks execute asynchronously to keep the interface responsive.



# Roadmap

### Version 1

* Voice assistant
* Dashboard
* Multi-provider routing
* Memory
* Plugin framework
* Self-learning
* Local-first execution



### Future Versions

* Autonomous long-running agents
* Computer vision
* Deep research workflows
* Coding copilot
* Autonomous software engineering
* Multi-device synchronization
* Swarm intelligence
* Full desktop automation
* Personalized AI ecosystem



# Project Goals

CRYOUS aims to become a truly personal AI operating system that can:

* Understand natural language
* Remember long-term context
* Learn new skills autonomously
* Coordinate specialized AI agents
* Control the computer safely
* Grow with every interaction

Rather than replacing existing AI models, CRYOUS brings them together under one intelligent orchestration layer.



# Contributing

Contributions are always welcome.

Whether you're fixing bugs, improving documentation, building plugins, or developing new agents, every contribution helps make CRYOUS better.

If you'd like to contribute:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a pull request.



# License

This project is released under the MIT License.

See the `LICENSE` file for more information.



# Final Note

CRYOUS is an ongoing effort to build an AI operating system that feels less like software and more like a capable digital partner.

The vision isn't just to answer questions—it is to understand, assist, automate, learn, and evolve alongside its user.
