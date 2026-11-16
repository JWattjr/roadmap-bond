type Provider = {
  request(args: { method: string; params?: unknown[] }): Promise<unknown>;
};

declare global {
  interface Window {
    ethereum?: Provider;
  }
}

export async function walletAccount() {
  const provider = window.ethereum;
  if (!provider) throw Error("Install MetaMask or a compatible wallet. Reading the board does not require a wallet.");
  const accounts = (await provider.request({ method: "eth_requestAccounts" })) as string[];
  if (!accounts[0]) throw Error("Choose an account in your wallet.");
  return { provider, account: accounts[0].toLowerCase() as `0x${string}` };
}

async function switchStudioNet(provider: Provider) {
  const chainId = "0xf22f";
  if (Number(await provider.request({ method: "eth_chainId" })) === 61999) return;
  try {
    await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId }] });
  } catch (error) {
    if ((error as { code?: number }).code !== 4902) throw error;
    await provider.request({
      method: "wallet_addEthereumChain",
      params: [{
        chainId,
        chainName: "GenLayer StudioNet",
        nativeCurrency: { name: "GEN", symbol: "GEN", decimals: 18 },
        rpcUrls: ["https://studio.genlayer.com/api"],
        blockExplorerUrls: ["https://explorer-studio.genlayer.com"],
      }],
    });
    await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId }] });
  }
  if (Number(await provider.request({ method: "eth_chainId" })) !== 61999) throw Error("Select GenLayer StudioNet in your wallet.");
}

export async function write(
  address: string,
  functionName: string,
  args: unknown[],
  value = BigInt(0),
) {
  const { provider: wallet, account } = await walletAccount();
  await switchStudioNet(wallet);
  const [{ createClient }, { studionet }] = await Promise.all([
    import("genlayer-js"),
    import("genlayer-js/chains"),
  ]);
  const bridge: Provider = {
    request: async (request) => {
      if (request.method !== "eth_sendTransaction") return wallet.request(request);
      const tx = request.params?.[0] as Record<string, unknown>;
      return wallet.request({
        ...request,
        params: [{ ...tx, chainId: "0xf22f", type: "0x0", gasPrice: "0x0", value: tx.value ?? "0x0" }],
      });
    },
  };
  const client = createClient({ chain: studionet, account, provider: bridge });
  const hash = await client.writeContract({
    address: address as `0x${string}`,
    functionName,
    args: args as never[],
    value,
  });
  if (typeof hash !== "string" || !/^0x[0-9a-fA-F]{64}$/.test(hash)) throw Error("Wallet returned no transaction hash. Check wallet activity before retrying.");
  return hash;
}
