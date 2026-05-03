// A simple WAV encoder for the browser
export class AudioRecorder {
  constructor() {
    this.stream = null;
    this.mediaRecorder = null;
    this.audioContext = null;
    this.processor = null;
    this.input = null;
    this.chunks = [];
    this.isRecording = false;
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    this.input = this.audioContext.createMediaStreamSource(this.stream);
    
    // Using a ScriptProcessor to manually create WAV chunks
    // (Note: ScriptProcessor is deprecated but highly compatible for this simple task)
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
    
    this.chunks = [];
    this.processor.onaudioprocess = (e) => {
      if (!this.isRecording) return;
      const channelData = e.inputBuffer.getChannelData(0);
      this.chunks.push(new Float32Array(channelData));
    };

    this.input.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
    this.isRecording = true;
  }

  async stop() {
    this.isRecording = false;
    
    if (this.processor) {
      this.processor.disconnect();
      this.input.disconnect();
    }
    
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
    }

    if (this.audioContext) {
      await this.audioContext.close();
    }

    return this.encodeWAV(this.chunks);
  }

  encodeWAV(chunks) {
    const length = chunks.reduce((acc, curr) => acc + curr.length, 0);
    const result = new Float32Array(length);
    let offset = 0;
    for (let chunk of chunks) {
      result.set(chunk, offset);
      offset += chunk.length;
    }

    const buffer = new ArrayBuffer(44 + result.length * 2);
    const view = new DataView(buffer);

    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    /* RIFF identifier */
    writeString(0, 'RIFF');
    /* file length */
    view.setUint32(4, 32 + result.length * 2, true);
    /* RIFF type */
    writeString(8, 'WAVE');
    /* format chunk identifier */
    writeString(12, 'fmt ');
    /* format chunk length */
    view.setUint32(16, 16, true);
    /* sample format (raw) */
    view.setUint16(20, 1, true);
    /* channel count */
    view.setUint16(22, 1, true);
    /* sample rate */
    view.setUint32(24, 16000, true);
    /* byte rate (sample rate * block align) */
    view.setUint32(28, 16000 * 2, true);
    /* block align (channel count * bytes per sample) */
    view.setUint16(32, 2, true);
    /* bits per sample */
    view.setUint16(34, 16, true);
    /* data chunk identifier */
    writeString(36, 'data');
    /* data chunk length */
    view.setUint32(40, result.length * 2, true);

    // Write samples
    offset = 44;
    for (let i = 0; i < result.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, result[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }

    return new Blob([buffer], { type: 'audio/wav' });
  }
}
