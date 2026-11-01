/** Uma consulta por painel; pausa cancela a requisição e descarta respostas antigas. */
export class LogPoller {
  private controller?: AbortController;
  private timer?: ReturnType<typeof setTimeout>;
  private active = false;
  private generation = 0;
  private fetchLogs: (signal: AbortSignal) => Promise<string>;
  private onData: (logs: string) => void;
  private onError: (error: unknown) => void;
  private interval: number;

  constructor(
    fetchLogs: (signal: AbortSignal) => Promise<string>,
    onData: (logs: string) => void,
    onError: (error: unknown) => void,
    interval = 2000,
  ) {
    this.fetchLogs = fetchLogs;
    this.onData = onData;
    this.onError = onError;
    this.interval = interval;
  }

  start() {
    if (this.active) return;
    this.active = true;
    void this.poll(++this.generation);
  }

  pause() {
    this.active = false;
    ++this.generation;
    clearTimeout(this.timer);
    this.controller?.abort();
  }

  private async poll(generation: number) {
    const controller = new AbortController();
    this.controller = controller;
    try {
      const logs = await this.fetchLogs(controller.signal);
      if (this.active && generation === this.generation) this.onData(logs);
    } catch (error) {
      if (this.active && generation === this.generation) this.onError(error);
    } finally {
      if (this.active && generation === this.generation) {
        this.timer = setTimeout(() => void this.poll(generation), this.interval);
      }
    }
  }
}
