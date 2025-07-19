document.addEventListener('DOMContentLoaded', () => {
  const withUserSelect = document.getElementById('with-user-select');
  const withUserInput = document.getElementById('with-user');
  const messageList = document.getElementById('message-list');
  const msgInput = document.getElementById('message-input');
  const sendBtn = document.getElementById('send-message-button');
  const newRecipient = document.getElementById('new-recipient');
  const newMessage = document.getElementById('new-message');
  const startBtn = document.getElementById('start-convo-button');
  const newError = document.getElementById('new-convo-error');
  const withUser = withUserInput ? withUserInput.value : '';

  async function loadMessages(user) {
    if (!user) return;
    try {
      const resp = await fetch(`/api/messages?user=${encodeURIComponent(user)}`);
      if (!resp.ok) return;
      const data = await resp.json();
      messageList.innerHTML = '';
      (data.messages || []).forEach(m => {
        const div = document.createElement('div');
        const ts = new Date(m.timestamp).toLocaleString();
        div.textContent = `${m.sender} (${ts}): ${m.message}`;
        messageList.appendChild(div);
      });
      await fetch('/api/messages/mark_read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user })
      });
    } catch (err) {
      console.error('Error loading messages:', err);
    }
  }

  if (withUser) {
    loadMessages(withUser);
  }

  if (withUserSelect) {
    withUserSelect.addEventListener('change', () => {
      const user = withUserSelect.value;
      if (user) {
        window.location.href = `/messages?user=${encodeURIComponent(user)}`;
      }
    });
  }

  if (sendBtn && withUser) {
    sendBtn.addEventListener('click', async () => {
      const text = msgInput.value.trim();
      if (!text) return;
      try {
        await fetch('/api/messages/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ recipient: withUser, message: text })
        });
        msgInput.value = '';
        loadMessages(withUser);
      } catch (err) {
        console.error('Error sending message:', err);
      }
    });
  }

  if (startBtn) {
    startBtn.addEventListener('click', async () => {
      const recipient = newRecipient.value.trim();
      const text = newMessage.value.trim();
      if (!recipient || !text) return;
      newError.textContent = '';
      try {
        const resp = await fetch('/api/messages/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ recipient, message: text })
        });
        if (resp.ok) {
          window.location.href = `/messages?user=${encodeURIComponent(recipient)}`;
        } else {
          const data = await resp.json().catch(() => null);
          newError.textContent = (data && data.detail) || 'Error sending message';
        }
      } catch (err) {
        console.error('Error sending message:', err);
        newError.textContent = 'Error sending message';
      }
    });
  }
});
