# AmaniQuery Documentation Index

> Central navigation hub for all AmaniQuery documentation. Organized by user journey and technical depth.

**Last Updated:** January 2026
**Documentation Version:** 2.0

---

## 🚀 Quick Start Path

**New to AmaniQuery? Start here:**

1. [Quick Start Guide](../QUICKSTART.md) - Get running in 5 minutes
2. [README](../README.md) - Overview and unique features
3. [Setup Script](../setup.py) - Automated installation

---

## 📚 Documentation by Category

### **For Users**

| Document | Description | Time to Read |
|----------|-------------|--------------|
| [README](../README.md) | Project overview with unique features | 5 min |
| [Quick Start](../QUICKSTART.md) | Installation and basic usage | 10 min |
| [InfoSMS Gateway Guide](SHARING_GUIDE.md) | SMS-based querying instructions | 5 min |
| [API Reference](../Module4_NiruAPI/) | Full API documentation | 30 min |
| [Constitutional Alignment Guide](CONSTITUTIONAL_ALIGNMENT.md) | Understanding legal analysis features | 15 min |

### **For Developers**

#### 🔧 Setup & Deployment
| Document | Description |
|----------|-------------|
| [Setup Script](../setup.py) | Automated environment setup |
| [Docker Guide](DOCKER_README.md) | Container deployment |
| [Deployment Guide](DEPLOYMENT_GUIDE.md) | Production deployment overview |
| [Deployment Implementation](DEPLOYMENT_IMPLEMENTATION_SUMMARY.md) | Step-by-step deployment |
| [Render Deployment](RENDER_DEPLOYMENT.md) | Render.com specific guide |
| [HuggingFace Deployment](HUGGINGFACE_DEPLOYMENT.md) | HuggingFace Spaces deployment |
| [Kubernetes Deployment](KUBERNETES_DEPLOYMENT.md) | K8s deployment |

#### 🏗️ Architecture
| Document | Description |
|----------|-------------|
| [V2 Architecture](AMANIQ_V2_ARCHITECTURE.md) | System architecture overview |
| [LangGraph Architecture](AMANIQ_V2_LANGGRAPH_ARCHITECTURE.md) | Agent-based architecture |
| [Constitutional Alignment](CONSTITUTIONAL_ALIGNMENT.md) | Legal analysis framework |
| [Response System](RESPONSE_SYSTEM.md) | Query response pipeline |
| [Session Auth Optimization](SESSION_AUTH_OPTIMIZATION.md) | Authentication system |
| [Auth Optimization](AUTH_OPTIMIZATION.md) | Security improvements |

#### 🔍 Module Documentation

**Module 1: Data Ingestion**
- [NiruSpider README](../Module1_NiruSpider/README.md) - Web crawling system

**Module 2: Data Processing**
- [NiruParser README](../Module2_NiruParser/README.md) - ETL and embeddings pipeline

**Module 3: Database**
- [NiruDB README](../Module3_NiruDB/README.md) - Vector database layer

**Module 4: API**
- [NiruAPI README](../Module4_NiruAPI/README.md) - REST API and GraphQL

**Module 5: Sharing**
- [NiruShare README](../Module5_NiruShare/README.md) - Sharing and collaboration features

**Module 6: Voice**
- [NiruVoice README](../Module6_NiruVoice/README.md) - Voice interaction

**Module 7: Hybrid**
- [NiruHybrid README](../Module7_NiruHybrid/README.md) - Hybrid query processing

**Module 8: Auth**
- [NiruAuth README](../Module8_NiruAuth/README.md) - Authentication and authorization

**Module 9: Sense**
- [NiruSense README](../Module9_NiruSense/README.md) - Sentiment and analysis

#### 🛠️ Development
| Document | Description |
|----------|-------------|
| [Contributing Guide](../CONTRIBUTING.md) | How to contribute |
| [Research Reports](RESEARCH_REFACTOR.md) | Research mode architecture |
| [Vision & Multimedia](VISION_MULTIMEDIA_MODULE.md) | Vision capabilities |
| [Offline Resilience](OFFLINE_RESILIENCE.md) | Offline functionality |
| [Data Upload](DATA_UPLOAD_README.md) | Manual data upload guide |
| [Moonshot Setup](MOONSHOT_SETUP.md) | Moonshot AI integration |

---

## 🎯 Use Case Guides

### **Legal & Constitutional Analysis**
- [Constitutional Alignment Guide](CONSTITUTIONAL_ALIGNMENT.md)
- [Legal Content Processing](../Module1_NiruSpider/README.md#kenya-law-spider)

### **Parliamentary Intelligence**
- [Parliament Data Sources](../Module1_NiruSpider/README.md#parliament-spider)
- [Video Indexer Feature](../README.md#3-parliament-video-indexer)

### **News & Sentiment Analysis**
- [News RSS Feeds](../Module1_NiruSpider/README.md#news-rss-spider)
- [Sentiment Gauge Feature](../README.md#1-public-sentiment-gauge)
- [Global Trends](../Module1_NiruSpider/README.md#global-trends-spider)

### **Accessibility & SMS**
- [InfoSMS Gateway](../README.md#2-infosms-gateway-kabambe-accessibility)
- [Sharing Guide](SHARING_GUIDE.md)

---

## 🔍 Finding Information

### **Search by Topic**

| Topic | Key Documents |
|-------|---------------|
| **Installation** | [Quick Start](../QUICKSTART.md), [Setup](../setup.py), [Docker](DOCKER_README.md) |
| **Deployment** | [Deployment Guide](DEPLOYMENT_GUIDE.md), [Render](RENDER_DEPLOYMENT.md), [HuggingFace](HUGGINGFACE_DEPLOYMENT.md) |
| **Architecture** | [V2 Architecture](AMANIQ_V2_ARCHITECTURE.md), [LangGraph](AMANIQ_V2_LANGGRAPH_ARCHITECTURE.md) |
| **Legal Analysis** | [Constitutional Alignment](CONSTITUTIONAL_ALIGNMENT.md), [Module1 README](../Module1_NiruSpider/README.md) |
| **API** | [API Docs](../Module4_NiruAPI/), [Response System](RESPONSE_SYSTEM.md) |
| **Security** | [Security](../SECURITY.md), [Auth Optimization](AUTH_OPTIMIZATION.md) |
| **Development** | [Contributing](../CONTRIBUTING.md), [Research](RESEARCH_REFACTOR.md) |

### **Search by Role**

**Legal Researchers:**
→ [README](../README.md) → [Constitutional Alignment](CONSTITUTIONAL_ALIGNMENT.md) → [Quick Start](../QUICKSTART.md)

**Backend Developers:**
→ [V2 Architecture](AMANIQ_V2_ARCHITECTURE.md) → [Module API Docs](../Module4_NiruAPI/) → [Deployment](DEPLOYMENT_GUIDE.md)

**Frontend Developers:**
→ [README](../README.md) → [Frontend](../frontend/) → [API Reference](../Module4_NiruAPI/)

**DevOps Engineers:**
→ [Docker Guide](DOCKER_README.md) → [Deployment Guide](DEPLOYMENT_GUIDE.md) → [K8s](KUBERNETES_DEPLOYMENT.md)

**Contributors:**
→ [Contributing](../CONTRIBUTING.md) → [Architecture](AMANIQ_V2_ARCHITECTURE.md) → [Module READMEs](../Module1_NiruSpider/README.md)

---

## 📖 Documentation Standards

This documentation follows the [Documentation Templates](../.agent/skills/documentation-templates/SKILL.md) guidelines:

- ✅ **Scannable**: Headers, lists, tables for quick scanning
- ✅ **Examples First**: Show, don't just tell
- ✅ **Progressive Detail**: Simple → Complex
- ✅ **Up to Date**: Current as of January 2026

### **Documentation Principles**

| Principle | Application |
|-----------|-------------|
| **Clear Navigation** | TOC, categories, cross-references |
| **Consistent Structure** | Standard templates per doc type |
| **Use Case Focused** | Organized by user journey |
| **Maintainable** | Clear update points and versioning |

---

## 🔄 Documentation Updates

### **Version History**

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | Jan 2026 | Complete restructure with documentation index |
| 1.0 | 2025 | Initial documentation set |

### **Update Process**

1. Update relevant doc file
2. Update this index with new/removed docs
3. Update cross-references
4. Increment documentation version if major changes

---

## 📞 Getting Help

**Issues/Questions:**
- Check this documentation index
- Review relevant module README
- See [Contributing](../CONTRIBUTING.md) for communication channels

**Missing Documentation:**
- Please open an issue to request new docs
- Follow patterns in this index for consistency

---

## 🏁 Next Steps

**Choose your path:**

1. **Explore Features** → Start with [README](../README.md)
2. **Get Running** → Jump to [Quick Start](../QUICKSTART.md)
3. **Understand Architecture** → Read [V2 Architecture](AMANIQ_V2_ARCHITECTURE.md)
4. **Dive into Code** → Browse [Module READMEs](../Module1_NiruSpider/README.md)

---

<div align="center">

**AmaniQuery** • Democratizing Legal Access in Kenya 🇰🇪

[← Back to README](../README.md) | [Quick Start →](../QUICKSTART.md)

</div>
