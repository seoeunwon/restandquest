// Minimal Web Speech API typings we use

interface SpeechRecognitionAlternative {
    transcript: string;
    confidence: number;
}

interface SpeechRecognitionResult {
    readonly length: number;
    readonly isFinal: boolean;
    [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionResultList {
    readonly length: number;
    [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionEvent extends Event {
    readonly resultIndex: number;
    readonly results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
    error: string;
    message: string;
}

declare class SpeechRecognition {
    lang: string;
    continuous: boolean;
    interimResults: boolean;
    maxAlternatives: number;

    onstart: ((this: SpeechRecognition, ev: Event) => void) | null;
    onend: ((this: SpeechRecognition, ev: Event) => void) | null;
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null;

    start(): void;
    stop(): void;
    abort(): void;
}

declare class webkitSpeechRecognition extends SpeechRecognition {}

interface Window {
    SpeechRecognition?: { new (): SpeechRecognition };
    webkitSpeechRecognition?: { new (): SpeechRecognition };
}