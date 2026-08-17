/**
 * Spatial Audio Helper for OrionAI
 * Uses Web Audio API PannerNode to create directional audio.
 */

class SpatialAudioController {
    constructor() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.listener = this.audioContext.listener;
        this.panner = this.audioContext.createPanner();
        
        // Configure Panner
        this.panner.panningModel = 'HRTF';
        this.panner.distanceModel = 'inverse';
        this.panner.refDistance = 1;
        this.panner.maxDistance = 10000;
        this.panner.rolloffFactor = 1;
        this.panner.coneInnerAngle = 360;
        this.panner.coneOuterAngle = 0;
        this.panner.coneOuterGain = 0;

        // Position Listener at center
        if (this.listener.positionX) {
            this.listener.positionX.setValueAtTime(0, this.audioContext.currentTime);
            this.listener.positionY.setValueAtTime(0, this.audioContext.currentTime);
            this.listener.positionZ.setValueAtTime(0, this.audioContext.currentTime);
        } else {
            this.listener.setPosition(0, 0, 0);
        }
    }

    /**
     * Update the bot's "head" position in 3D space
     * @param {number} x - Range [-1, 1] (Left to Right)
     * @param {number} y - Range [-1, 1] (Top to Bottom)
     * @param {number} z - Range [0, 1] (Depth)
     */
    updatePosition(x, y, z = 1) {
        const xPos = x * 5; // Scaling for audible panning
        const yPos = -y * 5;
        const zPos = -z * 5;

        if (this.panner.positionX) {
            this.panner.positionX.setTargetAtTime(xPos, this.audioContext.currentTime, 0.1);
            this.panner.positionY.setTargetAtTime(yPos, this.audioContext.currentTime, 0.1);
            this.panner.positionZ.setTargetAtTime(zPos, this.audioContext.currentTime, 0.1);
        } else {
            this.panner.setPosition(xPos, yPos, zPos);
        }
    }

    /**
     * Play an audio buffer through the panner
     * @param {ArrayBuffer} arrayBuffer 
     */
    async play(arrayBuffer) {
        const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        
        // Connect nodes: Source -> Panner -> Destination
        source.connect(this.panner);
        this.panner.connect(this.audioContext.destination);
        
        source.start(0);
        return source;
    }

    resume() {
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
    }
}

export const spatialAudio = new SpatialAudioController();
