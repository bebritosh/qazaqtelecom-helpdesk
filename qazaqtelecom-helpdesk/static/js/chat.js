(function () {
  const messagesEl = document.getElementById('chat-messages');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const fileInput = document.getElementById('file-input');
  const btnVoice = document.getElementById('btn-voice');
  const filePreview = document.getElementById('file-preview');

  if (!messagesEl || !form || !input) return;

  function appendMessage(text, isBot, imageUrl = null) {
    const wrapper = document.createElement('div');
    wrapper.className = 'd-flex mb-3 ' + (isBot ? '' : 'justify-content-end');

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble ' + (isBot ? 'msg-bot' : 'msg-user');
    
    if (imageUrl) {
      const img = document.createElement('img');
      img.src = imageUrl;
      img.className = 'img-fluid rounded mb-2';
      img.style.maxWidth = '200px';
      bubble.appendChild(img);
    }
    
    if (text) {
      const textNode = document.createElement('div');
      textNode.textContent = text;
      bubble.appendChild(textNode);
    }

    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function showTypingIndicator() {
    const wrapper = document.createElement('div');
    wrapper.className = 'd-flex mb-3';
    wrapper.id = 'typing-indicator';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble msg-bot';
    bubble.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
    bubble.style.padding = '0.75rem 1.25rem';

    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
  }

  appendMessage('Здравствуйте! Я ИИ-помощник Казахтелеком. Опишите вашу проблему, и я помогу найти решение.', true);

  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          if (filePreview) {
            filePreview.innerHTML = `
              <div class="position-relative d-inline-block">
                <img src="${event.target.result}" class="img-thumbnail" style="max-width: 100px; max-height: 100px;">
                <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 rounded-circle" 
                        style="width: 24px; height: 24px; padding: 0;" onclick="this.parentElement.parentElement.innerHTML=''; document.getElementById('file-input').value='';">
                  <i class="bi bi-x"></i>
                </button>
              </div>
            `;
            filePreview.style.display = 'block';
          }
        };
        reader.readAsDataURL(file);
      }
    });
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = input.value.trim();
    const hasFile = fileInput && fileInput.files[0];
    
    if (!text && !hasFile) return;

    let imagePreviewUrl = null;
    if (hasFile) {
      imagePreviewUrl = URL.createObjectURL(fileInput.files[0]);
    }

    appendMessage(text, false, imagePreviewUrl);
    input.value = '';
    if (filePreview) filePreview.style.display = 'none';

    showTypingIndicator();

    const formData = new FormData();
    formData.append('text', text);
    if (hasFile) {
      formData.append('image', fileInput.files[0]);
      fileInput.value = '';
    }

    const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]');
    
    fetch('/tickets/api/chat/', {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken ? csrfToken.value : ''
      },
      body: formData,
    })
      .then(res => {
        if (!res.ok) throw new Error('Network error');
        return res.json();
      })
      .then(data => {
        hideTypingIndicator();
        if (data && data.reply) {
          setTimeout(() => appendMessage(data.reply, true), 300);
        }
      })
      .catch(() => {
        hideTypingIndicator();
        appendMessage('Произошла ошибка. Попробуйте ещё раз или обратитесь к оператору.', true);
      });
  });

  if (btnVoice && 'webkitSpeechRecognition' in window) {
    const Recognition = window.webkitSpeechRecognition;
    const recognition = new Recognition();
    recognition.lang = 'ru-RU';
    recognition.interimResults = false;

    btnVoice.addEventListener('click', () => {
      btnVoice.innerHTML = '<span class="loading-spinner"></span>';
      recognition.start();
    });

    recognition.addEventListener('result', (event) => {
      const transcript = event.results[0][0].transcript;
      input.value = transcript;
      input.focus();
      btnVoice.innerHTML = '<i class="bi bi-mic"></i>';
    });

    recognition.addEventListener('error', () => {
      btnVoice.innerHTML = '<i class="bi bi-mic"></i>';
    });

    recognition.addEventListener('end', () => {
      btnVoice.innerHTML = '<i class="bi bi-mic"></i>';
    });
  }

  const style = document.createElement('style');
  style.textContent = `
    .typing-dots { display: flex; gap: 4px; }
    .typing-dots span {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: rgba(255,255,255,0.7);
      animation: typing 1.4s infinite;
    }
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typing {
      0%, 60%, 100% { transform: translateY(0); opacity: 0.7; }
      30% { transform: translateY(-10px); opacity: 1; }
    }
  `;
  document.head.appendChild(style);
})();
