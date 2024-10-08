// Copyright (c) 2024 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

import React from 'react';
import Modal from 'components/Common/Modal';
import styled from 'styled-components';
import PropTypes from 'prop-types';
import { toXec } from 'wallet';
import { supportedFiatCurrencies } from 'config/cashtabSettings';
import { TokenIconExpandButton } from 'components/Etokens/Token/styled';
import { token as tokenConfig } from 'config/token';

const MODAL_HEIGHT = 500;
export const OfferTable = styled.div`
    display: flex;
    flex-wrap: wrap;
    flex-direction: row;
    justify-content: center;
    width: 100%;
    gap: 9px;
    background-color: transparent;
    border-radius: 9px;
    color: ${props => props.theme.contrast};
    overflow: auto;
    &::-webkit-scrollbar {
        width: 12px;
    }

    &::-webkit-scrollbar-track {
        -webkit-box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.3);
        background-color: ${props => props.theme.eCashBlue};
        border-radius: 10px;
        height: 80%;
    }

    &::-webkit-scrollbar-thumb {
        border-radius: 10px;
        color: ${props => props.theme.eCashBlue};
        -webkit-box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.5);
    }
`;
export const OfferIcon = styled.div`
    display: flex;
    width: 128px;
    height: 128px;
    background: url(${props =>
            `${tokenConfig.tokenIconsUrl}/${props.size}/${props.tokenId}.png`})
        center no-repeat;
    background-size: 100% 100%;
    transition: all ease-in-out 1s;
    :hover {
        background-size: 150% 150%;
    }
`;
export const OfferRow = styled.div`
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 3px;
    align-items: center;
    justify-content: center;
`;
export const OfferCol = styled.div`
    width: 30%;
    min-width: 128px;
    display: flex;
    flex-direction: column;
`;

const BrowseCollection = ({
    collectionTokenId,
    agoraOffers,
    cashtabCache,
    settings,
    userLocale,
    fiatPrice,
    handleCancel,
    handleNftIconClick,
    listingsBelongToThisWallet,
}) => {
    const cachedCollectionInfo = cashtabCache.tokens.get(collectionTokenId);
    const collectionName =
        typeof cachedCollectionInfo !== 'undefined'
            ? cachedCollectionInfo.genesisInfo.tokenName
            : `${collectionTokenId.slice(0, 3)}...${collectionTokenId.slice(
                  -3,
              )}`;

    return (
        <Modal
            title={
                listingsBelongToThisWallet
                    ? `Manage your NFTs in ${collectionName}`
                    : `Listed NFTs in "${collectionName}"`
            }
            height={MODAL_HEIGHT}
            showButtons={false}
            handleCancel={handleCancel}
        >
            <OfferTable>
                {agoraOffers.map(offer => {
                    const thisNftTokenId = offer.token.tokenId;
                    const cachedNftInfo =
                        cashtabCache.tokens.get(thisNftTokenId);
                    const nftName =
                        typeof cachedNftInfo !== 'undefined'
                            ? cachedNftInfo.genesisInfo.tokenName
                            : `${thisNftTokenId.slice(
                                  0,
                                  3,
                              )}...${thisNftTokenId.slice(-3)}`;

                    // For offers generated by Cashtab, the price is always
                    // the value at the index-1 enforced output
                    // TODO we may need to add a more robust check here for offers
                    // generated outside of Cashtab
                    const priceXec = toXec(
                        parseInt(offer.variant.params.enforcedOutputs[1].value),
                    );

                    return (
                        <OfferCol key={thisNftTokenId}>
                            <OfferRow>
                                <TokenIconExpandButton
                                    aria-label={
                                        listingsBelongToThisWallet
                                            ? `Manage ${thisNftTokenId}`
                                            : `Buy ${thisNftTokenId}`
                                    }
                                    onClick={() =>
                                        handleNftIconClick(thisNftTokenId)
                                    }
                                >
                                    <OfferIcon
                                        title={nftName}
                                        size={128}
                                        tokenId={thisNftTokenId}
                                    />
                                </TokenIconExpandButton>
                            </OfferRow>

                            {typeof cachedNftInfo !== 'undefined' && (
                                <OfferRow>{nftName}</OfferRow>
                            )}

                            {fiatPrice !== null ? (
                                <OfferRow>
                                    {
                                        supportedFiatCurrencies[
                                            settings.fiatCurrency
                                        ].symbol
                                    }{' '}
                                    {(fiatPrice * priceXec).toLocaleString(
                                        userLocale,
                                        {
                                            minimumFractionDigits: 2,
                                            maximumFractionDigits: 2,
                                        },
                                    )}
                                </OfferRow>
                            ) : (
                                <OfferRow>
                                    {priceXec.toLocaleString(userLocale)} XEC
                                </OfferRow>
                            )}
                        </OfferCol>
                    );
                })}
            </OfferTable>
        </Modal>
    );
};

BrowseCollection.propTypes = {
    collectionTokenId: PropTypes.string,
    agoraOffers: PropTypes.array,
    cashtabCache: PropTypes.object,
    fiatPrice: PropTypes.number,
    settings: PropTypes.object,
    userLocale: PropTypes.string,
    handleCancel: PropTypes.func.isRequired,
    handleNftIconClick: PropTypes.func.isRequired,
    listingsBelongToThisWallet: PropTypes.bool,
};

export default BrowseCollection;
