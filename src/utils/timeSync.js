let offset = 0;
let synced = false;
let lastLatency = 0;

export const syncTimeWithServer = async () => {
  try {
    const start = Date.now();
    const response = await fetch('https://worldtimeapi.org/api/ip');
    const data = await response.json();
    const end = Date.now();
    
    lastLatency = (end - start) / 2;
    const externalTime = new Date(data.datetime).getTime() + lastLatency;
    const systemTime = Date.now();
    
    offset = externalTime - systemTime;
    synced = true;
    console.log(`[TimeSync] System offset: ${offset}ms, Latency: ${lastLatency}ms`);
    return offset;
  } catch (error) {
    console.warn("[TimeSync] Failed to sync time:", error);
    return 0;
  }
};

export const getSyncedDate = () => {
  return new Date(Date.now() + offset);
};

export const isTimeSynced = () => synced;
export const getTimeOffset = () => offset;
export const getLastLatency = () => lastLatency;
