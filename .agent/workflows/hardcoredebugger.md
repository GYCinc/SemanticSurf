---
description: In Depth Debug
---

# 🐛 **IDE + CLI DEBUGGING WAR ROOM**
## *Solo Developer Edition - Terminal-First Approach*

---

## **🛠️ TERMINAL PREP (2 min)**
```bash
# Quick setup - run once
mkdir -p ~/.debugtools
echo 'export DEBUG_HOME=~/.debugtools' >> ~/.zshrc

# Essential aliases
cat >> ~/.zshrc << 'EOF'
# Debugging shortcuts
alias buglog='cd ~/.debugtools && code .'
alias memwatch='htop'
alias netwatch='lsof -Pni | grep LISTEN'
alias portkill='lsof -ti:3000 | xargs kill -9'
alias jsdebug='node --inspect-brk'
alias pydebug='python -m pdb'
alias resetenv='rm -rf node_modules && npm install'
alias testbug='npm test -- --grep'
EOF

source ~/.zshrc
```

---

## **🔍 STEP 1: REPRODUCE (5 min)**

### **1.1 Quick Environment Snapshot:**
```bash
# Run in project root
echo "=== BUG REPORT $(date) ===" > bug_report.md
echo "OS: $(uname -a)" >> bug_report.md
echo "Node: $(node -v)" >> bug_report.md
echo "NPM: $(npm -v)" >> bug_report.md
echo "Git: $(git rev-parse --short HEAD)" >> bug_report.md
npm list --depth=0 >> bug_report.md
```

### **1.2 Minimal Reproduction:**
```bash
# Create isolated test
mkdir -p /tmp/bugtest_$(date +%s)
cd /tmp/bugtest_*

# Copy minimal files needed
cp ~/project/package.json .
cp ~/project/src/buggyfile.js .
npm install --silent

# Test in clean environment
NODE_ENV=test node buggyfile.js
```

---

## **📍 STEP 2: ISOLATE (3-10 min)**

### **2.1 Git Bisect Fast:**
```bash
# Quick blame for recent changes
git log --oneline -20
git blame buggyfile.js | head -20

# Binary search manually:
# 1. Comment out half your code
# 2. Test
# 3. Still broken? Keep that half, repeat
# 4. Fixed? Switch to other half
```

### **2.2 Dependency Check:**
```bash
# Check if it's a dependency issue
npm ls | grep -E "(error|missing)"
npm outdated

# Test with fresh install
mv node_modules node_modules.backup
npm cache clean --force
npm install
```

---

## **🔬 STEP 3: INSPECT (5-15 min)**

### **3.1 Smart Console Logging:**
```javascript
// Quick debugging template
const debug = {
  log: (label, value) => {
    console.log(`🔍 ${label}:`, 
      typeof value === 'object' ? JSON.stringify(value, null, 2) : value,
      '\n📞 Caller:', new Error().stack.split('\n')[2]
    );
  },
  time: (label) => {
    console.time(`⏱️  ${label}`);
    return () => console.timeEnd(`⏱️  ${label}`);
  }
};

// Usage:
debug.log('user', user);
const endTimer = debug.time('api-call');
// ... code ...
endTimer();
```

### **3.2 Terminal Debugging Tools:**
```bash
# Watch file changes and auto-test
nodemon --exec 'node --inspect=0.0.0.0:9229 buggyfile.js'

# Network debugging
curl -v http://localhost:3000/api/buggy
http --verbose GET http://localhost:3000/api/buggy

# Memory quick check
node --expose-gc -e "console.log(process.memoryUsage())"
```

### **3.3 Process Inspection:**
```bash
# What's running?
ps aux | grep node
pstree -p | grep -A 5 -B 5 node

# What files are open?
lsof -p $(pgrep node)

# CPU usage
top -pid $(pgrep node)
```

---

## **🤔 STEP 4: HYPOTHESIZE (2-5 min)**

### **Mental Checklist:**
1. **What changed recently?** 
   ```bash
   git diff HEAD~5
   ```

2. **Is it timing-related?**
   ```bash
   # Add delay
   sleep 1 && node script.js
   ```

3. **Is it async?**
   ```javascript
   // Wrap promises
   Promise.resolve(yourCode()).catch(e => console.error('Async error:', e));
   ```

4. **Is it data-specific?**
   ```bash
   # Test with minimal data
   echo '{"test": true}' | node script.js
   ```

### **Quick Theories Test:**
```bash
# Theory 1: Race condition
for i in {1..10}; do node buggy.js & done

# Theory 2: Memory issue
node --max-old-space-size=512 buggy.js

# Theory 3: Permission issue
sudo -u nobody node buggy.js
```

---

## **🔧 STEP 5: VERIFY & FIX (5-20 min)**

### **5.1 Safe Fix Approach:**
```bash
# Before fixing
git stash save "before-fix-$(date +%s)"
git checkout -b fix/bug-description

# Make minimal change
# Test immediately
npm test

# If passes, commit
git add .
git commit -m "fix: description of fix

- Root cause: [brief]
- Fix: [what changed]
- Tests: [what was tested]
"
```

### **5.2 Quick Verification Script:**
```bash
#!/bin/bash
# verify.sh
echo "🧪 Testing fix..."

echo "1. Unit tests:"
npm test 2>&1 | tail -20

echo "2. Lint check:"
npm run lint 2>&1 | tail -10

echo "3. Build test:"
npm run build 2>&1 | tail -10

echo "4. Manual test:"
# Add your manual test command here
curl -s http://localhost:3000/health | grep ok

echo "✅ Verification complete"
```

---

## **🛡️ STEP 6: PREVENT (3-10 min)**

### **6.1 Quick Prevention Measures:**

#### **Add Test Case:**
```bash
# Create test file
cat > test/bug-fix.test.js << 'EOF'
describe('Bug fix: [description]', () => {
  it('should not [original bug behavior]', async () => {
    // Test that would have caught the bug
    const result = await buggyFunction();
    expect(result).toBeDefined();
  });
});
EOF
```

#### **Add Logging:**
```bash
# Add debug logging to catch future occurrences
cat >> src/buggy-area.js << 'EOF'
// Debug logging for future issues
if (process.env.DEBUG_BUGGY_AREA) {
  console.log('[DEBUG] Buggy area state:', {
    timestamp: new Date().toISOString(),
    // Add relevant state variables
  });
}
EOF
```

#### **Update Documentation:**
```bash
# Add to README or internal docs
cat >> TROUBLESHOOTING.md << 'EOF'
## Bug: [Description]
- **Symptoms**: [What you see]
- **Root Cause**: [What was wrong]
- **Fix**: [What fixed it]
- **Prevention**: [How to avoid in future]
EOF
```

### **6.2 One-Time Prevention Setup:**
```bash
# Set up basic monitoring
cat > scripts/health-check.sh << 'EOF'
#!/bin/bash
# Daily health check
curl -f http://localhost:3000/health || echo "Service down!" | mail -s "ALERT" you@email.com
EOF
chmod +x scripts/health-check.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 9 * * * cd ~/project && ./scripts/health-check.sh") | crontab -
```

---

## **🚀 DEBUGGING WORKFLOW SUMMARY**

### **Quick Reference Card:**
```
1️⃣ REPRODUCE (5min)
   $ mkdir /tmp/bugtest && cd $_
   $ cp ~/project/{package.json,buggy.js} .
   $ npm install && node buggy.js

2️⃣ ISOLATE (3min)
   $ git log --oneline -10
   $ npm ls | grep error
   # Comment out half the code

3️⃣ INSPECT (5min)
   $ node --inspect buggy.js
   # Chrome: chrome://inspect
   # OR use debug.log() statements

4️⃣ HYPOTHESIZE (2min)
   - What changed? (git diff)
   - When does it fail? (add logs)
   - What's different? (compare env)

5️⃣ VERIFY (5min)
   $ git stash && git checkout -b fix/
   # Make minimal change
   $ npm test && git commit

6️⃣ PREVENT (3min)
   # Add test case
   # Update docs
   # Consider monitoring
```

### **Time Estimates:**
- **Simple bug**: 15-30 minutes total
- **Medium bug**: 30-60 minutes  
- **Complex bug**: 1-2 hours (consider asking for help)

---

## **🎯 PRO TIPS FOR SOLO DEBUGGING**

### **Mindset Hacks:**
1. **Timebox It**: 45 minutes max before taking a break
2. **Rubber Duck**: Explain the problem to your IDE (literally talk)
3. **Walk Away**: 5-minute walk often reveals the solution
4. **Change Context**: Switch to terminal-only or IDE-only mode

### **Terminal Power Moves:**
```bash
# Watch logs in real-time
tail -f error.log | grep -E "(ERROR|error|fail)"

# Find all occurrences of something
grep -r "buggyPattern" --include="*.js" --include="*.ts"

# Monitor file changes
watch -n 2 "ls -la node_modules | wc -l"

# Quick HTTP testing
http POST localhost:3000/api data:='{"test":true}'

# Check system resources while testing
top -d 1 -pid $(pgrep node) -stats pid,command,cpu,mem
```

### **IDE Shortcuts (VSCode):**
- `F5`: Start debugging
- `F9`: Toggle breakpoint  
- `F10`: Step over
- `F11`: Step into
- `Shift+F11`: Step out
- `Ctrl+Shift+D`: Debug sidebar
- `Ctrl+Shift+Y`: Debug console
- `Cmd+Shift+P` → "Debug: Start Debugging"

### **When Stuck (Escalation Path):**
1. **Take screenshot** of error
2. **Copy terminal output** to clipboard
3. **Search error message** (add "site:stackoverflow.com")
4. **Check GitHub issues** for similar problems
5. **Write question draft** (explaining often solves it)
6. **Sleep on it** (seriously, works 70% of time)

---

## **📊 DEBUGGING DASHBOARD (Optional)**
```bash
# Create a simple dashboard
cat > ~/.debugtools/dashboard.sh << 'EOF'
#!/bin/bash
clear
echo "=== DEBUG DASHBOARD ==="
echo "Memory:"
free -h | grep -E "^(Mem|Swap)"
echo ""
echo "Node Processes:"
ps aux | grep -E "(node|npm)" | grep -v grep
echo ""
echo "Open Ports:"
lsof -i -P -n | grep LISTEN | head -10
echo ""
echo "Recent Errors:"
tail -5 ~/.debugtools/error.log 2>/dev/null || echo "No error log"
EOF
chmod +x ~/.debugtools/dashboard.sh
```

Run with:
```bash
watch -n 2 ~/.debugtools/dashboard.sh
```

---

## **🌟 FINAL REMINDER**

**Debugging is a skill**, not magic. Each bug makes you better. 

**Success metrics:**
- ✅ Bug fixed
- ✅ Root cause understood  
- ✅ Test added
- ✅ Time wasted → Learning gained

**Now go squash some bugs!** 🐛💥