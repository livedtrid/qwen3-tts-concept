document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('tts-form');
  const apiKeyInput = document.getElementById('api-key');
  const userNameInput = document.getElementById('user-name');

  const submitBtn = document.getElementById('submit-btn');
  const btnText = submitBtn.querySelector('.btn-text');
  const spinner = submitBtn.querySelector('.spinner');

  const resultContainer = document.getElementById('result-container');
  const audioPlayer = document.getElementById('audio-player');
  const downloadBtn = document.getElementById('download-btn');

  const errorContainer = document.getElementById('error-container');
  const errorMessage = document.getElementById('error-message');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const apiKey = apiKeyInput.value.trim();
    const userName = userNameInput.value.trim();

    if (!apiKey || !userName) {
      showError('Please provide both an API key and your name.');
      return;
    }

    // Reset UI state
    hideError();
    resultContainer.classList.add('hidden');

    // Set loading state
    setLoading(true);

    try {
      const audioUrl = await generateAudio(apiKey, userName);

      // Update UI with result
      audioPlayer.src = audioUrl;
      downloadBtn.href = audioUrl;

      // Auto-play might be blocked by browsers, but we load it
      audioPlayer.load();

      resultContainer.classList.remove('hidden');

    } catch (error) {
      console.error('TTS Error:', error);
      showError(error.message || 'Failed to generate audio. Please check your API key and try again.');
    } finally {
      setLoading(false);
    }
  });

  async function generateAudio(apiKey, userName) {
    // The DashScope API blocks browser origins due to CORS policy to protect API keys.
    // We bypass this using cors-anywhere for this frontend PoC.
    const targetAPI = 'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation';
    const endpoint = 'https://cors-anywhere.herokuapp.com/' + targetAPI;

    const textToSynthesize = `Hola ${userName}, haz las maletas y prepárate para el Mundial de Fútbol de 2026, pues eres uno de los convocados.`;

    const payload = {
      model: 'qwen3-tts-flash',
      input: {
        text: textToSynthesize,
        voice: 'Ryan',
        language_type: 'Spanish' // Specified as per API documentation
      }
    };

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      if (response.status === 403 && response.url.includes("cors-anywhere.herokuapp.com")) {
        throw new Error('CORS Anywhere needs temporary access. Open a new tab, go to: https://cors-anywhere.herokuapp.com/corsdemo, click "Request temporary access to the demo server", then try again here.');
      }
      let errorDetails = '';
      try {
        const errorJson = await response.json();
        errorDetails = errorJson.message || errorJson.code;
      } catch (e) {
        // Ignored
      }
      throw new Error(`API returned ${response.status}: ${errorDetails || response.statusText}`);
    }

    const data = await response.json();

    if (data.output && data.output.audio && data.output.audio.url) {
      return data.output.audio.url;
    } else {
      throw new Error('Unexpected response format from the API.');
    }
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
