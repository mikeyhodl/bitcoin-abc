const config = require('./config');
module.exports = {
    parseBlock: function (chronikBlockResponse) {
        const { blockInfo, txs } = chronikBlockResponse;
        const { hash } = blockInfo;
        const { height, numTxs } = blockInfo;
        const parsedTxs = [];
        for (let i = 0; i < txs.length; i += 1) {
            parsedTxs.push(module.exports.parseTx(txs[i]));
        }
        return { hash, height, numTxs, parsedTxs };
    },
    parseTx: function (tx) {
        /*
Parse an eCash tx as returned by chronik for interesting information

Model
{ opreturn: '', isTokenTx: true, fromAddress: '', toAddress: '', isGenesisTx: true, isCoinbaseTx: true }

Assumptions
- input[0] is the sending address
- any input addresses are potential change addresses
- Assume total outputs not at input addresses are "sent" amounts
*/
        let isTokenTx = false;
        let isGenesisTx = false;
        let genesisInfo = false;
        if (tx.slpTxData !== null && typeof tx.slpTxData !== 'undefined') {
            isTokenTx = true;
            if (
                tx.slpTxData.slpMeta !== null &&
                typeof tx.slpTxData.slpMeta !== 'undefined' &&
                tx.slpTxData.genesisInfo !== null &&
                typeof tx.slpTxData.genesisInfo !== 'undefined' &&
                tx.slpTxData.slpMeta.txType === 'GENESIS'
            ) {
                isGenesisTx = true;
                genesisInfo = tx.slpTxData.genesisInfo;
            }
        }
        return { isTokenTx, isGenesisTx, genesisInfo };
    },
    getBlockTgMessage: function (parsedBlock) {
        const { hash, height, numTxs, parsedTxs } = parsedBlock;

        // Iterate over parsedTxs to find anything newsworthy
        let tokenTxCount = 0;
        let genesisTxCount = 0;
        const genesisInfoArray = [];
        for (let i = 0; i < parsedTxs.length; i += 1) {
            const thisParsedTx = parsedTxs[i];
            const { isTokenTx, isGenesisTx, genesisInfo } = thisParsedTx;
            if (isTokenTx) {
                tokenTxCount += 1;
                if (isGenesisTx) {
                    genesisTxCount += 1;
                    genesisInfoArray.push(genesisInfo);
                }
            }
        }
        const tgMsg =
            `<a href="${
                config.blockExplorer
            }/block/${hash}">${height}</a> | ${numTxs} tx${
                numTxs > 1 ? `s` : ''
            }\n` +
            `\n` +
            (tokenTxCount > 0
                ? `${tokenTxCount} eToken tx${tokenTxCount > 1 ? `s` : ''}\n` +
                  (genesisTxCount > 0
                      ? `\n` +
                        `This block created ${genesisTxCount} new eToken${
                            tokenTxCount > 1 ? `s` : ''
                        }:\n` +
                        `\n` +
                        `${genesisInfoArray
                            .map(genesisInfo => {
                                const {
                                    tokenTicker,
                                    tokenName,
                                    tokenDocumentUrl,
                                } = genesisInfo;
                                return `${tokenName} (${tokenTicker}) <a href="${tokenDocumentUrl}">[doc]</a>`;
                            })
                            .join('\n')}`
                      : '')
                : '');

        return tgMsg;
    },
};