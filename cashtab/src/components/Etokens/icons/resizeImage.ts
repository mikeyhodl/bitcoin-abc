// Copyright (c) 2024 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

import { createImage, ReaderResult } from './cropImage';

export default async function getResizedImg(
    imageSrc: string,
    callback: (result: ReaderResult) => void,
    fileName: string,
): Promise<void> {
    const image = await createImage(imageSrc);

    const width = 512;
    const height = 512;
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    if (ctx === null) {
        throw new Error('no ctx');
    }

    ctx.drawImage(image, 0, 0, width, height);
    if (!HTMLCanvasElement.prototype.toBlob) {
        Object.defineProperty(HTMLCanvasElement.prototype, 'toBlob', {
            value: function (
                callback: (blob: Blob) => void,
                type: string,
                quality: number,
            ) {
                const dataURL = this.toDataURL(type, quality).split(',')[1];
                setTimeout(function () {
                    const binStr = atob(dataURL),
                        len = binStr.length,
                        arr = new Uint8Array(len);
                    for (let i = 0; i < len; i++) {
                        arr[i] = binStr.charCodeAt(i);
                    }
                    callback(new Blob([arr], { type: type || 'image/png' }));
                });
            },
        });
    }

    return new Promise(resolve => {
        ctx.canvas.toBlob(
            blob => {
                if (blob === null) {
                    throw new Error('blob is null');
                }
                const file = new File([blob], fileName, {
                    type: 'image/png',
                });
                const resultReader = new FileReader();

                resultReader.readAsDataURL(file);

                resultReader.addEventListener('load', () =>
                    callback({ file, url: resultReader.result as string }),
                );
                resolve();
            },
            'image/png',
            1,
        );
    });
}
