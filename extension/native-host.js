const TOGGLE_COMMAND = "toggle";
const COLLAPSE_COMMAND = "collapse";

const nativeHostContract = fetch(
  chrome.runtime.getURL("native-host-contract.json"),
).then(async (response) => {
  const contract = await response.json();
  if (contract.schema_version !== 1) {
    throw new Error("Unsupported native host contract");
  }
  return contract;
});

export async function toggleVerticalTabs() {
  const contract = await nativeHostContract;
  await sendCommand(contract.name, TOGGLE_COMMAND);
}

export async function collapseVerticalTabs() {
  const contract = await nativeHostContract;
  await sendCommand(contract.name, COLLAPSE_COMMAND);
}

async function sendCommand(hostName, command) {
  const response = await chrome.runtime.sendNativeMessage(
    hostName,
    { command },
  );
  if ("error" in response) {
    throw new Error(response.error);
  }
}
