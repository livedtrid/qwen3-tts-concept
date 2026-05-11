document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('tts-form');
  const userNameInput = document.getElementById('user-name');

  const submitBtn = document.getElementById('submit-btn');
  const btnText = submitBtn.querySelector('.btn-text');
  const spinner = submitBtn.querySelector('.spinner');

  const resultContainer = document.getElementById('result-container');
  const audioPlayer = document.getElementById('audio-player');
  const downloadBtn = document.getElementById('download-btn');

  const errorContainer = document.getElementById('error-container');
  const errorMessage = document.getElementById('error-message');

  // Revoke any previous object URL to avoid memory leaks
  let currentObjectUrl = null;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const userName = userNameInput.value.trim();
    if (!userName) {
      showError('Please enter your name.');
      return;
    }

    hideError();
    resultContainer.classList.add('hidden');

    // Revoke previous audio blob
    if (currentObjectUrl) {
      URL.revokeObjectURL(currentObjectUrl);
      currentObjectUrl = null;
    }

    setLoading(true);

    try {
      const audioUrl = await generateAudio(userName);

      audioPlayer.src = audioUrl;
      downloadBtn.href = audioUrl;
      audioPlayer.load();

      resultContainer.classList.remove('hidden');
    } catch (error) {
      console.error('TTS Error:', error);
      showError(error.message || 'Failed to generate audio. Make sure the server is running.');
    } finally {
      setLoading(false);
    }
  });

  async function generateAudio(userName) {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: userName }),
    });

    if (!response.ok) {
      let errorDetails = '';
      try {
        const errorJson = await response.json();
        errorDetails = errorJson.error || errorJson.message;
      } catch (_) {
        // ignore parse error
      }
      throw new Error(errorDetails || `Server returned ${response.status}: ${response.statusText}`);
    }

    const blob = await response.blob();
    currentObjectUrl = URL.createObjectURL(blob);
    return currentObjectUrl;
  }

  function setLoading(isLoading) {
    if (isLoading) {
      submitBtn.disabled = true;
      btnText.textContent = 'Please wait...';
      spinner.classList.remove('hidden');
    } else {
      submitBtn.disabled = false;
      btnText.textContent = 'Generate Audio';
      spinner.classList.add('hidden');
    }
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorContainer.classList.remove('hidden');
  }

  function hideError() {
    errorContainer.classList.add('hidden');
    errorMessage.textContent = '';
  }
});
