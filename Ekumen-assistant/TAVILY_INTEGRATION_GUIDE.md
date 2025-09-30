# Tavily Integration Guide

**Last Updated:** 2025-09-30  
**Status:** ✅ Fully Configured and Working

---

## ✅ Current Status

### **1. Tavily is Already Configured**

Your Tavily integration is **fully set up and working**:

- ✅ **API Key configured** in `.env` file
- ✅ **TavilyService** implemented at `app/services/tavily_service.py`
- ✅ **Internet Agent** using Tavily for web search
- ✅ **Supplier Agent** using Tavily for supplier search
- ✅ **Test suite** available at `test_tavily_integration.py`

### **2. API Key**

```bash
TAVILY_API_KEY=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
```

This is configured in `Ekumen-assistant/.env` (line 16)

---

## 🔧 Two Ways to Use Tavily

### **Option 1: Direct Python Integration** (✅ Already Working)

Your application uses Tavily directly via the Python SDK. This is what you have now.

**How it works:**
1. `TavilyService` (`app/services/tavily_service.py`) wraps the Tavily Python client
2. `InternetAgent` and `SupplierAgent` use this service
3. Agents are called from your chat service when users activate Internet or Supplier mode

**No additional setup needed** - this is already working!

### **Option 2: MCP Integration** (for Claude Desktop)

The MCP URL you provided (`https://mcp.tavily.com/mcp/?tavilyApiKey=...`) is for **Claude Desktop app**, not your Python application.

**What is MCP?**
- MCP = Model Context Protocol
- Allows Claude Desktop to use external tools
- Separate from your Python application

**To use MCP with Claude Desktop:**

1. **Find your Claude Desktop config file:**
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add this configuration:**
   ```json
   {
     "mcpServers": {
       "tavily": {
         "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=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"
       }
     }
   }
   ```

3. **Restart Claude Desktop**

**Note:** This is **separate** from your Ekumen application. It only affects Claude Desktop app.

---

## 📊 Current Integration Architecture

### **Services:**

**`app/services/tavily_service.py`** - Main Tavily service
- `search_internet()` - General web search
- `search_suppliers()` - Find agricultural suppliers
- `search_market_prices()` - Get commodity prices
- `search_news()` - Agricultural news

### **Agents:**

**`app/agents/internet_agent.py`** - Internet mode
- Handles general web search queries
- Detects query type (prices, news, general)
- Routes to appropriate Tavily method
- Formats results for chat

**`app/agents/supplier_agent.py`** - Supplier mode
- Finds agricultural suppliers
- Extracts location from query
- Prioritizes French agricultural sites
- Formats supplier information

### **Integration Points:**

1. **Tool Registry** (`app/services/tool_registry_service.py`)
   - Lines 179-180: Imports Internet and Supplier agents
   - Used in `execute_tools_parallel()` method

2. **Agent Manager** (`app/agents/agent_manager.py`)
   - Manages agent routing
   - Activates agents based on user mode

---

## 🚀 How to Use Tavily in Your App

### **1. Test Tavily Integration**

```bash
cd Ekumen-assistant
python test_tavily_integration.py
```

This will run 6 tests:
1. Service availability
2. Internet search
3. Supplier search
4. Market prices
5. Internet Agent
6. Supplier Agent

### **2. Use in Chat**

**Internet Mode:**
```
User: "Quelles sont les dernières actualités agricoles en France?"
→ Internet Agent activates
→ Uses Tavily to search web
→ Returns formatted results
```

**Supplier Mode:**
```
User: "Où puis-je acheter des semences de maïs près de Bordeaux?"
→ Supplier Agent activates
→ Uses Tavily to find suppliers
→ Returns supplier list with URLs
```

**Market Prices:**
```
User: "Quel est le prix du blé aujourd'hui?"
→ Internet Agent activates
→ Detects price query
→ Uses Tavily market price search
→ Returns current prices
```

### **3. Programmatic Usage**

```python
from app.services.tavily_service import get_tavily_service

# Get service
tavily = get_tavily_service()

# Check availability
if tavily.is_available():
    # Search internet
    result = await tavily.search_internet(
        query="prix du blé France 2024",
        max_results=5
    )
    
    # Search suppliers
    result = await tavily.search_suppliers(
        query="fournisseur semences",
        location="Bordeaux",
        max_results=5
    )
    
    # Search market prices
    result = await tavily.search_market_prices(
        commodity="blé",
        region="Nouvelle-Aquitaine",
        max_results=5
    )
    
    # Search news
    result = await tavily.search_news(
        topic="agriculture biologique",
        max_results=5
    )
```

---

## 🔍 Tavily Features Used

### **Search Depth:**
- `"advanced"` - Comprehensive results (used for suppliers, prices)
- `"basic"` - Quick results (used for news)

### **Domain Filtering:**

**Supplier Search:**
- `agriconomie.com`
- `agrizone.net`
- `terralto.com`
- `agriaffaires.com`
- `pages-jaunes.fr`

**Market Prices:**
- `terre-net.fr`
- `lafranceagricole.fr`
- `agri-mutuel.com`
- `agritel.com`
- `euronext.com`

**News:**
- `lafranceagricole.fr`
- `terre-net.fr`
- `agri-mutuel.com`
- `pleinchamp.com`
- `web-agri.fr`

### **Response Features:**
- ✅ AI-generated summary (`include_answer=True`)
- ✅ Relevance scores for each result
- ✅ Structured data (title, URL, content)
- ✅ Timestamp for freshness

---

## 📝 Configuration Files

### **1. Environment Variables** (`.env`)

```bash
# Tavily Search API (for Internet mode, Supplier mode, Market prices)
TAVILY_API_KEY=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
```

### **2. Config Service** (`app/core/config.py`)

```python
# Tavily Search API Configuration (for Internet mode, Supplier mode, Market prices)
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
```

### **3. Claude Desktop MCP** (Optional)

**File:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "tavily": {
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=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"
    }
  }
}
```

---

## ✅ Verification Checklist

- [x] Tavily API key in `.env` file
- [x] `TavilyService` implemented
- [x] `InternetAgent` using Tavily
- [x] `SupplierAgent` using Tavily
- [x] Test suite available
- [x] Agents registered in tool registry
- [x] Domain filtering configured
- [ ] MCP configured in Claude Desktop (optional)

---

## 🧪 Testing

### **Quick Test:**

```bash
cd Ekumen-assistant
python -c "
from app.services.tavily_service import get_tavily_service
tavily = get_tavily_service()
print('✅ Tavily available!' if tavily.is_available() else '❌ Not available')
print(f'API Key: {tavily.api_key[:20]}...')
"
```

### **Full Test Suite:**

```bash
python test_tavily_integration.py
```

Expected output:
```
✅ Tavily service is available
✅ Search successful!
✅ Supplier search successful!
✅ Market prices search successful!
✅ Internet Agent successful!
✅ Supplier Agent successful!

Tests Passed: 6/6
Success Rate: 100.0%
```

---

## 🎯 Summary

### **What You Have:**

1. ✅ **Tavily API key** configured
2. ✅ **TavilyService** - Wrapper for Tavily API
3. ✅ **InternetAgent** - Web search agent
4. ✅ **SupplierAgent** - Supplier search agent
5. ✅ **Test suite** - Comprehensive tests
6. ✅ **Domain filtering** - French agricultural sites prioritized

### **What You DON'T Need:**

- ❌ Additional setup for Python app (already done!)
- ❌ MCP configuration (unless you want Claude Desktop integration)
- ❌ Additional tools (agents handle everything)

### **Next Steps:**

1. **Test it:** Run `python test_tavily_integration.py`
2. **Use it:** Activate Internet or Supplier mode in chat
3. **Optional:** Configure MCP for Claude Desktop if you want

---

**Your Tavily integration is complete and ready to use! 🎉**

