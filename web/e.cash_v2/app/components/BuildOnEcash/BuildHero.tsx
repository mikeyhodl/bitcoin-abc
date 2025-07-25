// Copyright (c) 2025 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

"use client";
import React from "react";
import Image from "next/image";
import ContentContainer from "../Atoms/ContentContainer";
import GridPattern from "../Atoms/GridPattern";
import TrustedBy from "../Home/TrustedBy";
import { motion } from "framer-motion";

export default function BuildHero() {
  return (
    <div className="relative w-full pb-[100px] pt-[100px] lg:pt-[130px]">
      <div className="absolute inset-0 w-full opacity-70 lg:aspect-[1000/337]">
        <Image
          src="/bubble.png"
          alt="eCash"
          fill
          className="hidden lg:inline-block lg:object-contain"
        />
        <Image
          src="/bubble-mobile.png"
          alt="eCash"
          fill
          className="object-cover object-right lg:hidden"
        />
      </div>
      <div className="from-background absolute inset-0 w-full bg-gradient-to-t to-transparent lg:aspect-[1000/337]" />
      <GridPattern className="left-1/2 top-20 hidden -translate-x-[calc(50%-100px)] lg:inline-flex" />
      <ContentContainer>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="relative flex flex-col items-center text-center"
        >
          <div className="pink-gradient-text mb-4 text-sm font-light uppercase tracking-wide">
            BUILD
          </div>
          <h1 className="mb-6 max-w-[450px] text-center text-4xl font-bold tracking-tighter lg:text-6xl lg:leading-[60px]">
            Build on eCash to future-proof your tech
          </h1>
          <p className="lg:mb-30 text-secondaryText mx-auto mb-20 max-w-[450px] text-center text-base lg:text-lg">
            Become a pioneer in the eCash frontier economy. The eCash network's
            unique capabilities enable business models impossible anywhere else.
            Micropayments, novel tokenomics and on-chain trading — we're in
            uncharted territory.
          </p>
          <TrustedBy />
        </motion.div>
      </ContentContainer>
    </div>
  );
}
