// Copyright (c) 2023 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

'use strict';
const log = require('./log');
const config = require('../config');

module.exports = {
    initializeDb: async function (mongoClient) {
        // Use connect method to connect to the server
        await mongoClient.connect();
        log('Connected successfully to MongoDB server');
        const db = mongoClient.db(config.database.name);
        // Enforce unique aliases
        db.collection(config.database.collections.validAliases).createIndex(
            {
                alias: 1,
            },
            {
                unique: true,
            },
        );
        // Enforce unique txids, i.e. you cannot have the same txid in the db more than once
        db.collection(
            config.database.collections.confirmedTxHistory,
        ).createIndex(
            { txid: 1 },
            {
                unique: true,
            },
        );
        log(`Configured connection to database ${config.database.name}`);
        return db;
    },
};