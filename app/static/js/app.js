/**
 * NovaBank AI Banking Customer Assistant - Frontend Application Logic
 * Implements a modern ChatGPT / Gemini conversational banking experience.
 * Consumes the Phase 8 REST API:
 *   - POST /api/conversations
 *   - POST /api/chat
 *   - GET  /api/conversations/{conversation_id}
 *   - GET  /api/health
 * Phase 9 Implementation.
 */

(() => {
  'use strict';

  // Default verified NovaBank customers (grounded in data/customers.json)
  const REAL_CUSTOMERS = {
    'CUST001': { name: 'Arjun Nair', firstName: 'Arjun', initials: 'AN', occupation: 'Software Engineer', city: 'Mangalore' },
    'CUST002': { name: 'Priya Sharma', firstName: 'Priya', initials: 'PS', occupation: 'Data Analyst', city: 'Pune' },
    'CUST003': { name: 'Rohit Verma', firstName: 'Rohit', initials: 'RV', occupation: 'Business Owner', city: 'Delhi' },
    'CUST004': { name: 'Sneha Kulkarni', firstName: 'Sneha', initials: 'SK', occupation: 'UX Designer', city: 'Bengaluru' },
    'CUST005': { name: 'Vikram Patil', firstName: 'Vikram', initials: 'VP', occupation: 'Senior Manager', city: 'Mumbai' },
    'CUST006': { name: 'Ananya Reddy', firstName: 'Ananya', initials: 'AR', occupation: 'Doctor', city: 'Hyderabad' },
    'CUST007': { name: 'Karthik Iyer', firstName: 'Karthik', initials: 'KI', occupation: 'Chartered Accountant', city: 'Chennai' },
    'CUST008': { name: 'Meera Joshi', firstName: 'Meera', initials: 'MJ', occupation: 'Graduate Student', city: 'Jaipur' },
    'CUST009': { name: 'Suresh Menon', firstName: 'Suresh', initials: 'SM', occupation: 'Retired Teacher', city: 'Kochi' },
    'CUST010': { name: 'Divya Gupta', firstName: 'Divya', initials: 'DG', occupation: 'Marketing Manager', city: 'Lucknow' }
  };

  const customerDirectory = { ...REAL_CUSTOMERS };

  // Application State
  const state = {
    customerId: null,
    conversationId: null,
    conversations: [],
    messages: [],
    isLoading: false,
  };

  // DOM Elements
  const signinOverlay = document.getElementById('signin-overlay');
  const signinBtn = document.getElementById('signin-btn');
  const customerInput = document.getElementById('customer-id-input');
  const signinError = document.getElementById('signin-error');
  const signinErrorText = document.getElementById('signin-error-text');
  const demoPillsContainer = document.getElementById('demo-pills-container');
  const demoCountBadge = document.getElementById('demo-count-badge');
  const appLayout = document.getElementById('app-layout');
  const appSidebar = document.getElementById('app-sidebar');
  const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
  const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
  const sidebarBackdrop = document.getElementById('sidebar-backdrop');
  const newChatBtn = document.getElementById('new-chat-btn');
  const historyList = document.getElementById('history-list');
  const sidebarSignoutBtn = document.getElementById('sidebar-signout-btn');
  const topbarSignoutBtn = document.getElementById('topbar-signout-btn');
  const sidebarUserAvatar = document.getElementById('sidebar-user-avatar');
  const sidebarUserName = document.getElementById('sidebar-user-name');
  const sidebarUserId = document.getElementById('sidebar-user-id');
  const welcomeUserName = document.getElementById('welcome-user-name');
  const activeConvBadge = document.getElementById('active-conv-id');
  const systemStatus = document.getElementById('system-status');
  const errorBanner = document.getElementById('error-banner');
  const errorMessage = document.getElementById('error-message');
  const closeErrorBtn = document.getElementById('close-error-btn');
  const messagesContainer = document.getElementById('messages-container');
  const welcomeCard = document.getElementById('welcome-card');
  const loadingIndicator = document.getElementById('loading-indicator');
  const chatForm = document.getElementById('chat-form');
  const messageInput = document.getElementById('message-input');
  const sendBtn = document.getElementById('send-btn');
  const custPills = document.querySelectorAll('.cust-pill');
  const suggestionCards = document.querySelectorAll('.suggestion-card');

  // Policy Modal Elements
  const policyModal = document.getElementById('policy-modal');
  const modalPolicyTitle = document.getElementById('modal-policy-title');
  const modalPolicyCategory = document.getElementById('modal-policy-category');
  const modalPolicyFilename = document.getElementById('modal-policy-filename');
  const modalPolicySection = document.getElementById('modal-policy-section');
  const modalPolicyContent = document.getElementById('modal-policy-content');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modalDoneBtn = document.getElementById('modal-done-btn');

  /**
   * Initializes the application on DOM ready.
   */
  async function init() {
    setupEventListeners();
    await checkHealth();
    await loadCustomers();

    // Check localStorage for active signed-in customer
    const savedCustomerId = localStorage.getItem('novabank_customer_id');
    const savedConvId = localStorage.getItem('novabank_conversation_id');

    if (savedCustomerId) {
      customerInput.value = savedCustomerId;
      updateActiveCustPill(savedCustomerId);

      // Verify that the saved customer actually exists in database
      try {
        const verifyRes = await fetch(`/api/customers/${encodeURIComponent(savedCustomerId)}`);
        if (verifyRes.ok) {
          const custData = await verifyRes.json();
          const fullName = custData.name;
          const firstName = fullName.split(' ')[0];
          const initials = fullName.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase();

          customerDirectory[savedCustomerId] = {
            name: fullName,
            firstName: firstName,
            initials: initials,
            occupation: custData.occupation || '',
            city: custData.city || ''
          };

          state.customerId = savedCustomerId;
          if (sidebarUserAvatar) sidebarUserAvatar.textContent = initials;
          if (sidebarUserName) sidebarUserName.textContent = fullName;
          if (sidebarUserId) sidebarUserId.textContent = savedCustomerId;
          if (welcomeUserName) welcomeUserName.textContent = firstName;

          if (signinOverlay) signinOverlay.style.display = 'none';
          if (appLayout) appLayout.style.display = 'flex';

          const conversations = await loadConversationList(savedCustomerId);
          let targetConv = savedConvId;
          const hasSaved = targetConv && conversations.some(c => c.conversation_id === targetConv);

          if (hasSaved) {
            const restored = await loadConversationHistory(targetConv, savedCustomerId);
            if (restored) {
              updateActiveHistoryItem(targetConv);
              return;
            }
          }

          if (conversations.length > 0) {
            await switchConversation(conversations[0].conversation_id);
          } else {
            await startNewChat();
          }
          return;
        } else {
          // Stale or invalid customer in localStorage
          localStorage.removeItem('novabank_customer_id');
          localStorage.removeItem('novabank_conversation_id');
        }
      } catch {
        // Fallback to offline/mock
        await signInCustomer(savedCustomerId, false);
        return;
      }
    }

    // Not signed in: show authentication overlay
    showSignInScreen();
  }

  /**
   * Binds UI events.
   */
  function setupEventListeners() {
    // Sign In Button
    if (signinBtn) {
      signinBtn.addEventListener('click', async () => {
        const cid = getCustomerId();
        if (!cid) {
          showSignInError('Please enter a valid Customer ID (e.g. CUST001).');
          return;
        }
        await signInCustomer(cid, true);
      });
    }

    // Customer ID input: clear error on typing & handle Enter key
    if (customerInput) {
      customerInput.addEventListener('input', () => {
        hideSignInError();
      });
      customerInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const cid = getCustomerId();
          if (cid) {
            await signInCustomer(cid, true);
          } else {
            showSignInError('Please enter a valid Customer ID (e.g. CUST001).');
          }
        }
      });
    }

    // Sign Out Buttons (both sidebar & topbar)
    if (sidebarSignoutBtn) {
      sidebarSignoutBtn.addEventListener('click', signOutCustomer);
    }
    if (topbarSignoutBtn) {
      topbarSignoutBtn.addEventListener('click', signOutCustomer);
    }

    // Sidebar Toggles
    if (sidebarToggleBtn) {
      sidebarToggleBtn.addEventListener('click', () => {
        appSidebar.classList.toggle('open');
        sidebarBackdrop.classList.toggle('active');
      });
    }
    if (sidebarCloseBtn) {
      sidebarCloseBtn.addEventListener('click', closeSidebar);
    }
    if (sidebarBackdrop) {
      sidebarBackdrop.addEventListener('click', closeSidebar);
    }

    // New Chat Button
    if (newChatBtn) {
      newChatBtn.addEventListener('click', async () => {
        await startNewChat();
      });
    }

    // Customer Quick Select Pills in Login Screen
    custPills.forEach((pill) => {
      pill.addEventListener('click', () => {
        const selectedId = pill.getAttribute('data-cust');
        customerInput.value = selectedId;
        updateActiveCustPill(selectedId);
      });
    });

    // Form submission
    if (chatForm) {
      chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleSendMessage();
      });
    }

    // Keyboard handling: Enter to send, Shift+Enter for new line
    if (messageInput) {
      messageInput.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          await handleSendMessage();
        }
      });

      // Auto-resize textarea
      messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 140) + 'px';
      });
    }

    // Suggestion cards click
    suggestionCards.forEach((card) => {
      card.addEventListener('click', async () => {
        const query = card.getAttribute('data-query');
        if (query && !state.isLoading) {
          messageInput.value = query;
          messageInput.focus();
          await handleSendMessage();
        }
      });
    });

    // Close alert banner
    if (closeErrorBtn) {
      closeErrorBtn.addEventListener('click', hideError);
    }

    // Policy Document Viewer Modal Listeners
    if (modalCloseBtn) {
      modalCloseBtn.addEventListener('click', closePolicyModal);
    }
    if (modalDoneBtn) {
      modalDoneBtn.addEventListener('click', closePolicyModal);
    }
    if (policyModal) {
      policyModal.addEventListener('click', (e) => {
        if (e.target === policyModal) {
          closePolicyModal();
        }
      });
    }
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && policyModal && policyModal.style.display !== 'none') {
        closePolicyModal();
      }
    });
  }

  function closeSidebar() {
    if (appSidebar) appSidebar.classList.remove('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
  }

  /**
   * Shows error in the Sign-In overlay modal.
   */
  function showSignInError(msg) {
    if (signinErrorText) signinErrorText.textContent = msg;
    if (signinError) signinError.style.display = 'flex';
    if (customerInput) {
      customerInput.classList.add('error');
      customerInput.focus();
    }
  }

  /**
   * Hides error in the Sign-In overlay modal.
   */
  function hideSignInError() {
    if (signinError) signinError.style.display = 'none';
    if (customerInput) customerInput.classList.remove('error');
  }

  /**
   * Fetches real customers from /api/customers to populate demo pills and directory.
   */
  async function loadCustomers() {
    try {
      const res = await fetch('/api/customers');
      if (res.ok) {
        const list = await res.json();
        if (Array.isArray(list) && list.length > 0) {
          list.forEach((c) => {
            const cid = c.customer_id;
            const fullName = c.name || `Customer ${cid}`;
            const parts = fullName.split(' ');
            const firstName = parts[0];
            const initials = parts.map(p => p[0]).join('').slice(0, 2).toUpperCase() || cid.slice(0, 2);
            customerDirectory[cid] = {
              name: fullName,
              firstName: firstName,
              initials: initials,
              occupation: c.occupation || '',
              city: c.city || ''
            };
          });
          renderDemoPills(list);
        }
      }
    } catch (e) {
      console.warn('Unable to load customer directory:', e);
    }
  }

  /**
   * Dynamically renders demo customer pills with real data from customers.json.
   */
  function renderDemoPills(customers) {
    if (!demoPillsContainer) return;
    demoPillsContainer.innerHTML = '';
    const currentId = getCustomerId() || 'CUST001';

    customers.forEach((c) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `cust-pill ${c.customer_id === currentId ? 'active' : ''}`;
      btn.setAttribute('data-cust', c.customer_id);
      btn.setAttribute('data-name', c.name);

      const occ = c.occupation ? ` (${c.occupation})` : '';
      btn.innerHTML = `
        <span class="pill-id">${c.customer_id}</span>
        <span class="pill-name">${escapeHtml(c.name)}${escapeHtml(occ)}</span>
      `;

      btn.addEventListener('click', () => {
        customerInput.value = c.customer_id;
        hideSignInError();
        updateActiveCustPill(c.customer_id);
      });

      demoPillsContainer.appendChild(btn);
    });

    if (demoCountBadge) {
      demoCountBadge.textContent = `${customers.length} registered`;
    }
  }

  /**
   * Signs in the customer and transitions to the main chat layout.
   * Strictly validates that the customer ID exists in the database.
   */
  async function signInCustomer(customerId, isNewLogin = true) {
    hideSignInError();
    const cid = (customerId || '').trim().toUpperCase();
    if (!cid) {
      showSignInError('Please enter a valid Customer ID (e.g. CUST001).');
      return;
    }

    // STRICT VALIDATION: Check if customer exists in NovaBank database
    try {
      setLoading(true);
      const res = await fetch(`/api/customers/${encodeURIComponent(cid)}`);
      if (res.status === 404 || !res.ok) {
        setLoading(false);
        showSignInError(`Customer ID "${cid}" was not found. Please enter a valid NovaBank Customer ID (CUST001 to CUST010).`);
        return;
      }

      const custData = await res.json();
      setLoading(false);

      const fullName = custData.name || `Customer ${cid}`;
      const firstName = fullName.split(' ')[0];
      const initials = fullName.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase() || cid.slice(0, 2);

      customerDirectory[cid] = {
        name: fullName,
        firstName: firstName,
        initials: initials,
        occupation: custData.occupation || '',
        city: custData.city || ''
      };

      state.customerId = cid;
      localStorage.setItem('novabank_customer_id', cid);

      // Update UI with real customer data
      if (sidebarUserAvatar) sidebarUserAvatar.textContent = initials;
      if (sidebarUserName) sidebarUserName.textContent = fullName;
      if (sidebarUserId) sidebarUserId.textContent = cid;
      if (welcomeUserName) welcomeUserName.textContent = firstName;

      updateActiveCustPill(cid);

      // Transition views
      if (signinOverlay) signinOverlay.style.display = 'none';
      if (appLayout) appLayout.style.display = 'flex';

      // Load customer's past conversations with full isolation
      const conversations = await loadConversationList(cid);

      if (isNewLogin) {
        if (conversations.length > 0) {
          // Open latest conversation so customer can check and continue chatting
          await switchConversation(conversations[0].conversation_id);
        } else {
          await startNewChat();
        }
      }

      if (messageInput) messageInput.focus();
    } catch (err) {
      setLoading(false);
      console.error('Sign-in verification error:', err);
      showSignInError(`Connection error verifying Customer ID "${cid}". Please try again.`);
    }
  }

  /**
   * Signs out current customer and displays the sign-in screen.
   */
  function signOutCustomer() {
    state.customerId = null;
    state.conversationId = null;
    state.conversations = [];
    state.messages = [];

    localStorage.removeItem('novabank_customer_id');
    localStorage.removeItem('novabank_conversation_id');

    if (historyList) historyList.innerHTML = '';
    clearMessagesUI();
    showSignInScreen();
  }

  function showSignInScreen() {
    hideSignInError();
    if (appLayout) appLayout.style.display = 'none';
    if (signinOverlay) signinOverlay.style.display = 'flex';
    if (customerInput) {
      customerInput.focus();
      updateActiveCustPill(customerInput.value);
    }
  }

  /**
   * Returns current sanitized customer ID from input.
   */
  function getCustomerId() {
    return (customerInput.value || '').trim().toUpperCase();
  }

  /**
   * Updates visual active state on customer pills.
   */
  function updateActiveCustPill(customerId) {
    const pills = document.querySelectorAll('.cust-pill');
    pills.forEach((p) => {
      if (p.getAttribute('data-cust') === customerId) {
        p.classList.add('active');
      } else {
        p.classList.remove('active');
      }
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Checks API health via GET /api/health.
   */
  async function checkHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'ok' && systemStatus) {
          systemStatus.className = 'status-badge status-online';
          const txt = systemStatus.querySelector('.status-text');
          if (txt) txt.textContent = 'System Online';
        }
      }
    } catch {
      // offline handling
    }
  }

  /**
   * Resets the active view to a fresh new chat session without saving empty sessions.
   * If already in a new empty chat, prevents creating duplicate empty chats.
   * Empty chats are never persisted to the server or history list until a message is sent.
   */
  async function startNewChat() {
    const cid = state.customerId || getCustomerId();
    if (!cid) {
      showSignInScreen();
      return;
    }

    closeSidebar();

    // If already in a new chat with 0 messages, do not create or duplicate anything
    if (!state.conversationId || state.messages.length === 0) {
      clearMessagesUI();
      if (welcomeCard) welcomeCard.style.display = 'block';
      if (messageInput) messageInput.focus();
      return;
    }

    // Clean up empty session on server if current conversation never had messages
    if (state.conversationId && state.messages.length === 0) {
      fetch(`/api/conversations/${encodeURIComponent(state.conversationId)}?customer_id=${encodeURIComponent(cid)}`, {
        method: 'DELETE',
      }).catch(() => {});
    }

    // Reset client state to fresh uncommitted conversation
    state.conversationId = null;
    state.messages = [];
    localStorage.removeItem('novabank_conversation_id');

    if (activeConvBadge) {
      activeConvBadge.textContent = 'New Chat';
      activeConvBadge.title = 'New Conversation';
    }

    updateActiveHistoryItem(null);
    clearMessagesUI();
    if (welcomeCard) welcomeCard.style.display = 'block';
    if (messageInput) messageInput.focus();
  }

  /**
   * Creates a new conversation session via POST /api/conversations.
   * Called on-demand when the user actually sends their first message.
   */
  async function createConversation(customerId) {
    if (!customerId) return;

    try {
      setLoading(true);
      hideError();

      const res = await fetch('/api/conversations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ customer_id: customerId }),
      });

      if (res.status === 201) {
        const data = await res.json();
        state.conversationId = data.conversation_id;
        state.messages = [];
        localStorage.setItem('novabank_conversation_id', data.conversation_id);

        if (activeConvBadge) {
          activeConvBadge.textContent = `${data.conversation_id.slice(0, 12)}...`;
          activeConvBadge.title = `Active Session: ${data.conversation_id}`;
        }

        clearMessagesUI();
      } else {
        showError('Unable to start a new chat session. Please try again.');
      }
    } catch {
      showError('Network error connecting to NovaBank services.');
    } finally {
      setLoading(false);
      if (messageInput) messageInput.focus();
    }
  }

  /**
   * Loads conversation history via GET /api/conversations/{id}?customer_id={cid}.
   */
  async function loadConversationHistory(conversationId, customerId) {
    try {
      const res = await fetch(
        `/api/conversations/${encodeURIComponent(conversationId)}?customer_id=${encodeURIComponent(customerId)}`,
        { headers: { 'Accept': 'application/json' } }
      );

      if (!res.ok) return false;

      const data = await res.json();
      state.conversationId = data.conversation_id;
      state.customerId = data.customer_id;
      state.messages = data.messages || [];

      if (activeConvBadge) {
        activeConvBadge.textContent = `${data.conversation_id.slice(0, 12)}...`;
        activeConvBadge.title = `Active Session: ${data.conversation_id}`;
      }

      clearMessagesUI();

      if (state.messages.length > 0) {
        hideWelcomeCard();
        state.messages.forEach((msg) => {
          renderMessageBubble(
            msg.role,
            msg.content,
            msg.sources || null,
            false,
            msg.thought_process || null,
            msg.execution_time_ms || null
          );
        });
        scrollToBottom();
      } else {
        if (welcomeCard) welcomeCard.style.display = 'block';
      }

      return true;
    } catch {
      return false;
    }
  }

  /**
   * Fetches customer's past conversation sessions via GET /api/conversations?customer_id={cid}.
   */
  async function loadConversationList(customerId) {
    if (!customerId) return [];
    try {
      const res = await fetch(`/api/conversations?customer_id=${encodeURIComponent(customerId)}`);
      if (res.ok) {
        const data = await res.json();
        state.conversations = data.conversations || [];
        renderConversationList();
        return state.conversations;
      }
    } catch (err) {
      console.warn('Failed to load conversation history:', err);
    }
    state.conversations = [];
    renderConversationList();
    return [];
  }

  /**
   * Dynamically renders the sidebar conversation history list.
   */
  function renderConversationList() {
    if (!historyList) return;
    historyList.innerHTML = '';

    if (!state.conversations || state.conversations.length === 0) {
      const emptyLi = document.createElement('li');
      emptyLi.className = 'history-empty-state';
      emptyLi.innerHTML = `
        <span>No past chats found.<br><small style="color: #64748b;">Start typing to begin a chat!</small></span>
      `;
      historyList.appendChild(emptyLi);
      return;
    }

    state.conversations.forEach((conv) => {
      // Never render empty conversations with 0 messages
      if (!conv.message_count || conv.message_count <= 0) return;

      const li = document.createElement('li');
      const isActive = conv.conversation_id === state.conversationId;
      li.className = `history-item ${isActive ? 'active' : ''}`;
      li.setAttribute('data-conv-id', conv.conversation_id);
      li.setAttribute('role', 'listitem');
      li.setAttribute('tabindex', '0');

      const timeLabel = formatRelativeTime(conv.updated_at || conv.created_at);
      const msgCountLabel = conv.message_count ? `${conv.message_count} msg${conv.message_count > 1 ? 's' : ''}` : 'New';

      li.innerHTML = `
        <div class="history-item-icon">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div class="history-item-body">
          <span class="history-title" title="${escapeHtml(conv.title || 'Conversation')}">${escapeHtml(conv.title || 'New Conversation')}</span>
          <div class="history-meta">
            <span class="history-time">${escapeHtml(timeLabel)}</span>
            <span>•</span>
            <span class="history-count">${escapeHtml(msgCountLabel)}</span>
          </div>
        </div>
        <button type="button" class="history-delete-btn" title="Delete conversation" aria-label="Delete conversation">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      `;

      // Click to switch conversation
      li.addEventListener('click', async (e) => {
        if (e.target.closest('.history-delete-btn')) return;
        await switchConversation(conv.conversation_id);
        closeSidebar();
      });

      // Enter key to switch
      li.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
          await switchConversation(conv.conversation_id);
          closeSidebar();
        }
      });

      // Delete button listener
      const deleteBtn = li.querySelector('.history-delete-btn');
      if (deleteBtn) {
        deleteBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          await deleteConversationSession(conv.conversation_id);
        });
      }

      historyList.appendChild(li);
    });
  }

  /**
   * Updates visual active class on the sidebar history item.
   */
  function updateActiveHistoryItem(convId) {
    if (!historyList) return;
    historyList.querySelectorAll('.history-item').forEach((item) => {
      if (item.getAttribute('data-conv-id') === convId) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }

  /**
   * Switches the active chat session to a previous conversation from history.
   */
  async function switchConversation(targetConvId) {
    if (!targetConvId || !state.customerId) return;
    if (state.conversationId === targetConvId && state.messages.length > 0) {
      return; // Already active
    }

    setLoading(true);
    hideError();

    state.conversationId = targetConvId;
    localStorage.setItem('novabank_conversation_id', targetConvId);

    if (activeConvBadge) {
      activeConvBadge.textContent = `${targetConvId.slice(0, 12)}...`;
      activeConvBadge.title = `Active Session: ${targetConvId}`;
    }

    updateActiveHistoryItem(targetConvId);

    const loaded = await loadConversationHistory(targetConvId, state.customerId);
    setLoading(false);

    if (!loaded || state.messages.length === 0) {
      if (welcomeCard) welcomeCard.style.display = 'block';
    } else {
      hideWelcomeCard();
    }

    if (messageInput) messageInput.focus();
  }

  /**
   * Deletes a conversation session from the sidebar and server.
   */
  async function deleteConversationSession(targetConvId) {
    if (!targetConvId || !state.customerId) return;

    const confirmDelete = window.confirm('Are you sure you want to delete this conversation?');
    if (!confirmDelete) return;

    try {
      const res = await fetch(
        `/api/conversations/${encodeURIComponent(targetConvId)}?customer_id=${encodeURIComponent(state.customerId)}`,
        { method: 'DELETE' }
      );

      if (res.ok) {
        state.conversations = state.conversations.filter(c => c.conversation_id !== targetConvId);

        if (state.conversationId === targetConvId) {
          if (state.conversations.length > 0) {
            await switchConversation(state.conversations[0].conversation_id);
          } else {
            await startNewChat();
          }
        } else {
          renderConversationList();
        }
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  }

  /**
   * Formats ISO timestamp to human-friendly relative time.
   */
  function formatRelativeTime(isoString) {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      if (isNaN(date.getTime())) return '';
      const now = new Date();
      const diffMs = now - date;
      const diffSecs = Math.floor(diffMs / 1000);
      const diffMins = Math.floor(diffSecs / 60);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffSecs < 60) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch {
      return '';
    }
  }

  /**
   * Handles user message sending.
   */
  async function handleSendMessage() {
    if (state.isLoading) return;

    const rawText = messageInput.value;
    const cleanText = (rawText || '').trim();

    if (!cleanText) {
      messageInput.focus();
      return;
    }

    if (!state.customerId) {
      showSignInScreen();
      return;
    }

    if (!state.conversationId) {
      await createConversation(state.customerId);
    }

    hideError();
    hideWelcomeCard();

    // Display user message immediately
    renderMessageBubble('user', cleanText, null, true);
    state.messages.push({
      role: 'user',
      content: cleanText,
    });
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Add or update the conversation in the sidebar history now that it has a message
    let activeItem = state.conversations.find(c => c.conversation_id === state.conversationId);
    let snippet = cleanText;
    if (snippet.length > 36) snippet = snippet.slice(0, 33) + '...';

    if (!activeItem) {
      activeItem = {
        conversation_id: state.conversationId,
        customer_id: state.customerId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        title: snippet,
        message_count: 1,
        last_message: cleanText,
      };
      state.conversations = [
        activeItem,
        ...state.conversations.filter(c => c.conversation_id !== state.conversationId),
      ];
    } else {
      if (activeItem.title === 'New Conversation' || !activeItem.message_count) {
        activeItem.title = snippet;
      }
      activeItem.message_count = (activeItem.message_count || 0) + 1;
      activeItem.updated_at = new Date().toISOString();
    }
    renderConversationList();

    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: state.conversationId,
          customer_id: state.customerId,
          message: cleanText,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        renderMessageBubble(
          'assistant',
          data.message,
          data.sources,
          true,
          data.thought_process,
          data.execution_time_ms
        );
        state.messages.push({
          role: 'assistant',
          content: data.message,
          sources: data.sources,
          thought_process: data.thought_process,
          execution_time_ms: data.execution_time_ms,
        });
        // Silently sync conversation list with server
        loadConversationList(state.customerId).catch(() => {});
      } else if (res.status === 404) {
        showError('Session expired. Starting a fresh conversation...');
        await createConversation(state.customerId);
      } else {
        showError('Unable to process your question. Please try again.');
      }
    } catch {
      showError('Unable to connect to NovaBank assistant. Please ensure the server is running.');
    } finally {
      setLoading(false);
      messageInput.focus();
    }
  }

  // Dynamic live agent thinking stages
  let thinkingInterval = null;
  const THINKING_STAGES = [
    'NovaBank Assistant is analyzing inquiry...',
    'Evaluating intent & checking customer credentials...',
    'Accessing banking tools & account records...',
    'Searching official NovaBank policy guidelines...',
    'Verifying facts & synthesizing grounded response...'
  ];

  /**
   * Sets loading state and disables/enables input controls with dynamic live status.
   */
  function setLoading(loading) {
    state.isLoading = loading;
    const thinkingLabel = loadingIndicator ? loadingIndicator.querySelector('.thinking-label') : null;

    if (loading) {
      if (loadingIndicator) loadingIndicator.style.display = 'flex';
      if (sendBtn) sendBtn.disabled = true;
      if (messageInput) messageInput.disabled = true;

      // Start live thinking status rotation
      let stageIdx = 0;
      if (thinkingLabel) thinkingLabel.textContent = THINKING_STAGES[0];
      if (thinkingInterval) clearInterval(thinkingInterval);
      thinkingInterval = setInterval(() => {
        stageIdx = (stageIdx + 1) % THINKING_STAGES.length;
        if (thinkingLabel) thinkingLabel.textContent = THINKING_STAGES[stageIdx];
      }, 1500);

      scrollToBottom();
    } else {
      if (thinkingInterval) {
        clearInterval(thinkingInterval);
        thinkingInterval = null;
      }
      if (thinkingLabel) thinkingLabel.textContent = 'NovaBank Assistant is thinking...';
      if (loadingIndicator) loadingIndicator.style.display = 'none';
      if (sendBtn) sendBtn.disabled = false;
      if (messageInput) messageInput.disabled = false;
    }
  }

  /**
   * Helper returning inline SVG bullet icon for thought steps.
   */
  function getStepBulletIcon(type) {
    switch (type) {
      case 'analysis':
        return `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`;
      case 'routing':
        return `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/></svg>`;
      case 'tool':
        return `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`;
      case 'rag':
        return `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`;
      case 'validation':
        return `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>`;
      case 'generation':
      default:
        return `<svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z"/></svg>`;
    }
  }

  /**
   * Opens the Policy Document Viewer modal, fetches markdown content, and highlights cited section/chunk.
   */
  async function openPolicyModal(filename, title = '', section = '', snippet = '') {
    if (!policyModal) return;

    const safeFilename = filename || 'document.md';
    const displayTitle = title || safeFilename.replace(/\.md$/i, '').replace(/^[0-9]+_/, '').replace(/_/g, ' ').toUpperCase();

    if (modalPolicyTitle) modalPolicyTitle.textContent = displayTitle;
    if (modalPolicyFilename) modalPolicyFilename.textContent = safeFilename;
    if (modalPolicyCategory) modalPolicyCategory.textContent = 'Knowledge Base';

    if (modalPolicySection) {
      if (section && section.trim()) {
        modalPolicySection.textContent = `📍 ${section}`;
        modalPolicySection.style.display = 'inline-flex';
      } else {
        modalPolicySection.style.display = 'none';
        modalPolicySection.textContent = '';
      }
    }

    if (modalPolicyContent) {
      modalPolicyContent.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:center; padding: 3.5rem 1rem; color: #64748b; gap: 0.75rem;">
          <svg style="animation: spin 1s linear infinite;" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="12" y1="2" x2="12" y2="6"/>
            <line x1="12" y1="18" x2="12" y2="22"/>
            <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
            <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
            <line x1="2" y1="12" x2="6" y2="12"/>
            <line x1="18" y1="12" x2="22" y2="12"/>
            <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>
            <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
          </svg>
          <span style="font-weight: 500;">Loading policy document from NovaBank Knowledge Base...</span>
        </div>
      `;
    }

    policyModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    try {
      const res = await fetch(`/api/policies/${encodeURIComponent(safeFilename)}`);
      if (res.ok) {
        const data = await res.json();
        if (modalPolicyTitle) modalPolicyTitle.textContent = data.title || displayTitle;
        if (modalPolicyCategory) modalPolicyCategory.textContent = data.category || 'Banking Policy';
        if (modalPolicyFilename) modalPolicyFilename.textContent = data.filename || safeFilename;
        if (modalPolicyContent) {
          modalPolicyContent.innerHTML = renderMarkdown(data.content);
          if (section || snippet) {
            highlightAndScrollToSection(modalPolicyContent, section, snippet);
          }
        }
      } else {
        if (modalPolicyContent) {
          modalPolicyContent.innerHTML = `
            <div style="padding: 2.5rem 1rem; text-align: center; color: #dc2626;">
              <p><strong>Document Not Found</strong></p>
              <p style="color: #64748b; font-size: 0.85rem; margin-top: 0.5rem;">Could not locate policy file "${escapeHtml(safeFilename)}".</p>
            </div>
          `;
        }
      }
    } catch {
      if (modalPolicyContent) {
        modalPolicyContent.innerHTML = `
          <div style="padding: 2.5rem 1rem; text-align: center; color: #dc2626;">
            <p><strong>Connection Error</strong></p>
            <p style="color: #64748b; font-size: 0.85rem; margin-top: 0.5rem;">Unable to load document from server.</p>
          </div>
        `;
      }
    }
  }

  /**
   * Highlights the specific cited section or chunk in the document modal and scrolls to it.
   */
  function highlightAndScrollToSection(container, targetSection, snippetText) {
    if (!container) return;

    // Remove any previous active highlights
    container.querySelectorAll('.cited-section-wrapper').forEach((el) => {
      const parent = el.parentNode;
      while (el.firstChild) {
        if (el.firstChild.classList && el.firstChild.classList.contains('cited-section-indicator-pill')) {
          el.removeChild(el.firstChild);
        } else {
          parent.insertBefore(el.firstChild, el);
        }
      }
      el.remove();
    });

    container.querySelectorAll('.cited-text-mark').forEach((el) => {
      const parent = el.parentNode;
      if (parent) {
        parent.replaceChild(document.createTextNode(el.textContent), el);
        parent.normalize();
      }
    });

    const cleanTarget = (targetSection || '').trim().toLowerCase();
    let matchedHeading = null;

    // 1. Search headings (H1 to H4)
    if (cleanTarget) {
      const headings = Array.from(container.querySelectorAll('h1, h2, h3, h4'));

      // Pass 1: exact or trimmed match
      for (const h of headings) {
        const text = (h.textContent || '').trim().toLowerCase();
        if (text === cleanTarget || text.replace(/^[0-9.]+\s*/, '') === cleanTarget.replace(/^[0-9.]+\s*/, '')) {
          matchedHeading = h;
          break;
        }
      }

      // Pass 2: substring or prefix match
      if (!matchedHeading) {
        for (const h of headings) {
          const text = (h.textContent || '').trim().toLowerCase();
          if (text.includes(cleanTarget) || cleanTarget.includes(text)) {
            matchedHeading = h;
            break;
          }
          const targetPrefix = cleanTarget.match(/^[0-9]+(\.[0-9]+)?/);
          const hPrefix = text.match(/^[0-9]+(\.[0-9]+)?/);
          if (targetPrefix && hPrefix && targetPrefix[0] === hPrefix[0]) {
            matchedHeading = h;
            break;
          }
        }
      }
    }

    // 2. If no heading matched, search content blocks for snippetText or section words
    let targetElement = matchedHeading;
    if (!targetElement && snippetText && snippetText.trim().length > 15) {
      const words = snippetText.trim().split(/\s+/).filter(w => w.length > 3).slice(0, 5);
      const searchPhrase = words.join(' ').toLowerCase();
      const blocks = Array.from(container.querySelectorAll('p, li, tr'));
      for (const b of blocks) {
        if ((b.textContent || '').toLowerCase().includes(searchPhrase)) {
          targetElement = b;
          break;
        }
      }
    }

    // Fallback: search for words in section title
    if (!targetElement && cleanTarget) {
      const words = cleanTarget.split(/\s+/).filter(w => w.length > 3);
      if (words.length > 0) {
        const blocks = Array.from(container.querySelectorAll('p, li, tr'));
        for (const b of blocks) {
          const bText = (b.textContent || '').toLowerCase();
          if (words.every(w => bText.includes(w))) {
            targetElement = b;
            break;
          }
        }
      }
    }

    // 3. Highlight and wrap the target section
    if (targetElement) {
      const wrapper = document.createElement('div');
      wrapper.className = 'cited-section-wrapper';

      const indicator = document.createElement('div');
      indicator.className = 'cited-section-indicator-pill';
      indicator.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
          <circle cx="12" cy="9" r="2.5"/>
        </svg>
        <span>Cited in Assistant Answer:</span>
      `;

      targetElement.parentNode.insertBefore(wrapper, targetElement);
      wrapper.appendChild(indicator);

      if (['H1', 'H2', 'H3', 'H4'].includes(targetElement.tagName)) {
        wrapper.appendChild(targetElement);
        let next = wrapper.nextSibling;
        let count = 0;
        while (next && count < 8) {
          if (next.nodeType === 1 && ['H1', 'H2', 'H3', 'H4'].includes(next.tagName)) {
            break;
          }
          const curr = next;
          next = next.nextSibling;
          wrapper.appendChild(curr);
          count++;
        }
      } else {
        wrapper.appendChild(targetElement);
      }

      // Mark matching snippet text inside the wrapper if available
      if (snippetText && snippetText.trim().length > 10) {
        const words = snippetText.trim().split(/\s+/).filter(w => w.length > 3);
        if (words.length >= 2) {
          const phrase = words.slice(0, 4).join(' ');
          highlightTextInside(wrapper, phrase);
        }
      }

      // Smoothly scroll the container to center the highlighted block
      setTimeout(() => {
        wrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 150);
    }
  }

  function highlightTextInside(root, phrase) {
    if (!root || !phrase) return;
    const lowerPhrase = phrase.toLowerCase();

    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
    const textNodes = [];
    let node;
    while ((node = walker.nextNode())) {
      if (node.nodeValue && node.nodeValue.toLowerCase().includes(lowerPhrase)) {
        textNodes.push(node);
      }
    }

    textNodes.forEach((tNode) => {
      const val = tNode.nodeValue;
      const idx = val.toLowerCase().indexOf(lowerPhrase);
      if (idx !== -1) {
        const before = val.slice(0, idx);
        const match = val.slice(idx, idx + phrase.length);
        const after = val.slice(idx + phrase.length);

        const span = document.createElement('span');
        if (before) span.appendChild(document.createTextNode(before));

        const mark = document.createElement('mark');
        mark.className = 'cited-text-mark';
        mark.textContent = match;
        span.appendChild(mark);

        if (after) span.appendChild(document.createTextNode(after));
        tNode.parentNode.replaceChild(span, tNode);
      }
    });
  }

  /**
   * Closes the Policy Document Viewer modal.
   */
  function closePolicyModal() {
    if (policyModal) {
      policyModal.style.display = 'none';
      document.body.style.overflow = '';
      if (modalPolicySection) {
        modalPolicySection.style.display = 'none';
        modalPolicySection.textContent = '';
      }
    }
  }

  /**
   * Renders a message bubble with collapsible thinking accordion and interactive citations.
   */
  function renderMessageBubble(role, content, sources = null, animate = true, thoughtProcess = null, executionTimeMs = null) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    if (!animate) row.style.animation = 'none';

    const header = document.createElement('div');
    header.className = 'message-header';
    header.textContent = role === 'user' ? 'You' : 'NovaBank Assistant';
    row.appendChild(header);

    // Collapsible Thinking Accordion for Assistant
    if (role === 'assistant' && Array.isArray(thoughtProcess) && thoughtProcess.length > 0) {
      const accordion = document.createElement('div');
      accordion.className = 'thought-accordion';

      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'thought-toggle';
      toggle.setAttribute('aria-expanded', 'false');

      const durationSec = (executionTimeMs && executionTimeMs > 0)
        ? (executionTimeMs / 1000).toFixed(1)
        : '1.2';

      toggle.innerHTML = `
        <div class="thought-toggle-left">
          <span class="thought-sparkle-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z"/>
            </svg>
          </span>
          <span class="thought-summary">Thought for ${durationSec} seconds</span>
        </div>
        <span class="thought-chevron">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </span>
      `;

      const drawer = document.createElement('div');
      drawer.className = 'thought-drawer';
      drawer.style.display = 'none';

      const timeline = document.createElement('div');
      timeline.className = 'thought-steps-timeline';

      thoughtProcess.forEach((step) => {
        const item = document.createElement('div');
        item.className = 'thought-step-item';

        const stepType = step.type || 'analysis';
        const badgeLabel = (step.type || 'step').toUpperCase();

        const bullet = document.createElement('div');
        bullet.className = `thought-step-bullet ${stepType}`;
        bullet.innerHTML = getStepBulletIcon(stepType);

        const body = document.createElement('div');
        body.className = 'thought-step-body';

        const stepHeader = document.createElement('div');
        stepHeader.className = 'thought-step-header';
        stepHeader.innerHTML = `
          <span class="thought-step-title">${escapeHtml(step.title || 'Step')}</span>
          <span class="thought-step-badge">${escapeHtml(badgeLabel)}</span>
        `;

        const desc = document.createElement('div');
        desc.className = 'thought-step-desc';
        desc.textContent = step.description || '';

        body.appendChild(stepHeader);
        body.appendChild(desc);
        item.appendChild(bullet);
        item.appendChild(body);
        timeline.appendChild(item);
      });

      drawer.appendChild(timeline);

      toggle.addEventListener('click', () => {
        const isExpanded = accordion.classList.toggle('expanded');
        toggle.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
        drawer.style.display = isExpanded ? 'block' : 'none';
      });

      accordion.appendChild(toggle);
      accordion.appendChild(drawer);
      row.appendChild(accordion);
    }

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    if (role === 'assistant') {
      bubble.classList.add('markdown-body');
      bubble.innerHTML = renderMarkdown(content);

      // Attach click listeners to any markdown links pointing to policies
      bubble.querySelectorAll('a').forEach((link) => {
        const href = link.getAttribute('href') || '';
        if (href.endsWith('.md') || href.includes('policy')) {
          link.classList.add('policy-doc-link');
          link.addEventListener('click', (e) => {
            e.preventDefault();
            const filename = href.split('/').pop();
            openPolicyModal(filename, link.textContent);
          });
        }
      });
    } else {
      bubble.textContent = content; // Safe text node preventing XSS
    }
    row.appendChild(bubble);

    // Provenance display & interactive citations (Collapsible Accordion)
    if (sources && Array.isArray(sources) && sources.length > 0) {
      const validSources = sources.filter(Boolean);
      const count = validSources.length;
      const countLabel = count === 1 ? '1 Source' : `${count} Sources`;

      const citationsContainer = document.createElement('div');
      citationsContainer.className = 'message-citations citations-accordion';

      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'citations-toggle';
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('title', 'Click to view cited sources');
      toggle.innerHTML = `
        <div class="citations-toggle-left">
          <span class="citations-book-icon">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </span>
          <span class="citations-label">Cited Sources</span>
          <span class="citations-count-pill">${countLabel}</span>
        </div>
        <span class="citations-chevron">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </span>
      `;

      const drawer = document.createElement('div');
      drawer.className = 'citations-drawer';
      drawer.style.display = 'none';

      const chipsContainer = document.createElement('div');
      chipsContainer.className = 'citation-chips';

      // Also maintain legacy .sources-container for backward compatibility
      const legacySources = document.createElement('div');
      legacySources.className = 'sources-container';
      legacySources.style.display = 'none';

      validSources.forEach((src) => {
        // Legacy badge
        const legacyBadge = document.createElement('span');
        if (src.type === 'tool') {
          legacyBadge.className = 'source-badge tool';
          legacyBadge.textContent = `Banking Tool: ${src.name || src.tool || 'Account API'}`;
        } else {
          legacyBadge.className = 'source-badge rag';
          legacyBadge.textContent = `Policy: ${src.source || src.title || 'Knowledge Base'}`;
        }
        legacySources.appendChild(legacyBadge);

        // Modern Interactive Citation Chip
        if (src.type === 'rag') {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'citation-chip policy-link';
          const filename = src.source || 'policy.md';
          const title = src.title || filename;
          const section = src.section || '';
          const snippet = src.snippet || '';
          const secText = section ? ` - ${section}` : '';
          btn.setAttribute('data-filename', filename);
          btn.setAttribute('data-title', title);
          if (section) btn.setAttribute('data-section', section);
          if (snippet) btn.setAttribute('data-snippet', snippet);
          btn.setAttribute('title', `Click to jump to ${section || title} in ${filename}`);
          btn.innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <span>${escapeHtml(filename)}${escapeHtml(secText)}</span>
            <span class="citation-open-icon">↗</span>
          `;
          btn.addEventListener('click', () => {
            openPolicyModal(filename, title, section, snippet);
          });
          chipsContainer.appendChild(btn);
        } else if (src.type === 'tool') {
          const span = document.createElement('span');
          span.className = 'citation-chip tool-link';
          span.innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
            <span>Banking Tool: ${escapeHtml(src.name || src.tool || 'Account API')}</span>
          `;
          chipsContainer.appendChild(span);
        }
      });

      drawer.appendChild(chipsContainer);

      toggle.addEventListener('click', () => {
        const isExpanded = citationsContainer.classList.toggle('expanded');
        toggle.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
        drawer.style.display = isExpanded ? 'block' : 'none';
      });

      citationsContainer.appendChild(toggle);
      citationsContainer.appendChild(drawer);
      row.appendChild(citationsContainer);
      row.appendChild(legacySources);
    }

    messagesContainer.appendChild(row);
    scrollToBottom();
  }

  function clearMessagesUI() {
    messagesContainer.innerHTML = '';
    messagesContainer.appendChild(welcomeCard);
    welcomeCard.style.display = 'block';
  }

  function hideWelcomeCard() {
    if (welcomeCard) welcomeCard.style.display = 'none';
  }

  function scrollToBottom() {
    const chatScroll = document.getElementById('chat-scroll-area');
    if (chatScroll) {
      chatScroll.scrollTop = chatScroll.scrollHeight;
    }
  }

  /**
   * Robust Markdown parser with fallback support.
   */
  function renderMarkdown(md) {
    if (!md) return '';

    const hasMarked =
      typeof window.marked !== 'undefined' &&
      (typeof window.marked.parse === 'function' || typeof window.marked === 'function');
    if (hasMarked) {
      try {
        const parseFn = typeof window.marked.parse === 'function' ? window.marked.parse.bind(window.marked) : window.marked;
        const html = parseFn(md, { breaks: true, gfm: true });
        if (typeof html === 'string' && html.trim().length > 0) {
          return sanitizeHtml(html);
        }
      } catch {
        // Fall back to built-in parser
      }
    }

    return parseMarkdownFallback(md);
  }

  function parseMarkdownFallback(text) {
    const lines = text.split('\n');
    const output = [];
    let inTable = false;
    let tableRows = [];
    let inList = false;
    let listItems = [];

    function flushTable() {
      if (tableRows.length > 0) {
        output.push(renderTableHtml(tableRows));
        tableRows = [];
        inTable = false;
      }
    }

    function flushList() {
      if (listItems.length > 0) {
        output.push('<ul>' + listItems.map(item => `<li>${item}</li>`).join('') + '</ul>');
        listItems = [];
        inList = false;
      }
    }

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        flushList();
        inTable = true;
        tableRows.push(trimmed);
        continue;
      } else if (inTable) {
        flushTable();
      }

      const listMatch = trimmed.match(/^[-*•]\s+(.*)$/);
      if (listMatch) {
        flushTable();
        inList = true;
        listItems.push(parseInline(listMatch[1]));
        continue;
      } else if (inList) {
        flushList();
      }

      if (!trimmed) continue;

      const h3Match = trimmed.match(/^###\s+(.*)$/);
      if (h3Match) {
        output.push(`<h3>${parseInline(h3Match[1])}</h3>`);
        continue;
      }

      const h2Match = trimmed.match(/^##\s+(.*)$/);
      if (h2Match) {
        output.push(`<h2>${parseInline(h2Match[1])}</h2>`);
        continue;
      }

      const h1Match = trimmed.match(/^#\s+(.*)$/);
      if (h1Match) {
        output.push(`<h1>${parseInline(h1Match[1])}</h1>`);
        continue;
      }

      output.push(`<p>${parseInline(trimmed)}</p>`);
    }

    flushTable();
    flushList();
    return output.join('\n');
  }

  function renderTableHtml(rows) {
    if (rows.length < 2) return '';
    let html = '<div class="table-container"><table>';
    let isHeader = true;

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      if (/^\|[-:\s|]+\|$/.test(row)) {
        isHeader = false;
        continue;
      }
      const cells = row.split('|').slice(1, -1).map(c => c.trim());
      html += '<tr>';
      cells.forEach(cell => {
        const tag = isHeader ? 'th' : 'td';
        html += `<${tag}>${parseInline(cell)}</${tag}>`;
      });
      html += '</tr>';
    }
    html += '</table></div>';
    return html;
  }

  function parseInline(str) {
    if (!str) return '';
    let s = str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    s = s.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*(.*?)\*/g, '<em>$1</em>');
    s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
    return s;
  }

  function sanitizeHtml(dirtyHtml) {
    if (typeof window.DOMPurify !== 'undefined' && typeof window.DOMPurify.sanitize === 'function') {
      return window.DOMPurify.sanitize(dirtyHtml);
    }
    return dirtyHtml.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  }

  function showError(msg) {
    if (errorMessage) errorMessage.textContent = msg;
    if (errorBanner) errorBanner.style.display = 'flex';
  }

  function hideError() {
    if (errorBanner) errorBanner.style.display = 'none';
  }

  // Self-initialization
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
