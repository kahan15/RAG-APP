function formatSources(sources) {
    if (!sources || sources.length === 0) return '';
    
    let sourceHtml = '<div class="sources-section mt-2">';
    sourceHtml += '<p class="text-sm text-gray-600 font-semibold">Sources:</p>';
    sourceHtml += '<ul class="list-disc pl-5 text-sm text-gray-600">';
    
    sources.forEach(source => {
        if (source.source === 'web') {
            // Handle web search results
            sourceHtml += `<li class="mb-1">
                <a href="${source.url}" target="_blank" class="text-blue-600 hover:underline">
                    ${source.title || 'Web Result'}
                </a>
                ${source.type === 'knowledge_graph' ? ' (Knowledge Graph)' : ''}
            </li>`;
        } else {
            // Handle local document sources
            sourceHtml += `<li class="mb-1">
                ${source.title || source.file || 'Document'}
                ${source.page ? ` (Page ${source.page})` : ''}
            </li>`;
        }
    });
    
    sourceHtml += '</ul></div>';
    return sourceHtml;
}

function appendMessage(message, isUser = false) {
    const chatContainer = document.getElementById('chat-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'} mb-4 ${isUser ? 'bg-blue-50' : 'bg-gray-50'} p-3 rounded-lg`;
    
    let messageContent = `<p class="text-gray-800">${marked.parse(message.content || '')}</p>`;
    
    if (!isUser && message.sources) {
        messageContent += formatSources(message.sources);
    }
    
    messageDiv.innerHTML = messageContent;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Initialize any code blocks with syntax highlighting
    messageDiv.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

// Web page ingestion form handler
document.getElementById('webForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const urlInput = document.getElementById('webUrl');
    const webButton = document.getElementById('webButton');
    const url = urlInput.value.trim();
    
    if (!url) return;
    
    toggleButton(webButton, true);
    addMessage('info', `Ingesting web page: ${url}`);
    
    try {
        const response = await fetch('/api/v1/ingest/webpage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });
        
        const data = await handleApiResponse(response);
        addMessage('info', 'Web page ingested successfully. You can now ask questions about its content.');
        urlInput.value = '';
        
        // Automatically ask a question about the ingested content
        const chatInput = document.getElementById('userInput');
        chatInput.value = `What is the main topic of this web page?`;
        document.getElementById('chatForm').dispatchEvent(new Event('submit'));
        
    } catch (error) {
        addMessage('error', `Failed to ingest web page: ${error.message}`);
    } finally {
        toggleButton(webButton, false);
    }
});

// Chat form handler
document.getElementById('chatForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const question = input.value.trim();
    
    if (!question) return;
    
    addMessage('user', question);
    input.value = '';
    toggleButton(sendButton, true);
    
    try {
        const response = await fetch('/api/v1/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                question,
                source_filter: null // Let the backend determine if we need web filtering
            })
        });
        
        const data = await handleApiResponse(response);
        addMessage('bot', data.answer, data.sources);
    } catch (error) {
        addMessage('error', `Error: ${error.message}`);
    } finally {
        toggleButton(sendButton, false);
    }
}); 