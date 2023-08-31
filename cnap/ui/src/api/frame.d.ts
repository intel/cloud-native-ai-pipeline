import * as $protobuf from "protobufjs";
import Long = require("long");
/** Properties of a FrameMessage. */
export interface IFrameMessage {

    /** FrameMessage pipelineId */
    pipelineId?: (string|null);

    /** FrameMessage sequence */
    sequence?: (number|Long|null);

    /** FrameMessage raw */
    raw?: (Uint8Array|null);

    /** FrameMessage tsNew */
    tsNew?: (number|null);

    /** FrameMessage rawHeight */
    rawHeight?: (number|null);

    /** FrameMessage rawWidth */
    rawWidth?: (number|null);

    /** FrameMessage rawChannels */
    rawChannels?: (number|null);

    /** FrameMessage tsInferEnd */
    tsInferEnd?: (number|null);
}

/** Represents a FrameMessage. */
export class FrameMessage implements IFrameMessage {

    /**
     * Constructs a new FrameMessage.
     * @param [properties] Properties to set
     */
    constructor(properties?: IFrameMessage);

    /** FrameMessage pipelineId. */
    public pipelineId: string;

    /** FrameMessage sequence. */
    public sequence: (number|Long);

    /** FrameMessage raw. */
    public raw: Uint8Array;

    /** FrameMessage tsNew. */
    public tsNew: number;

    /** FrameMessage rawHeight. */
    public rawHeight: number;

    /** FrameMessage rawWidth. */
    public rawWidth: number;

    /** FrameMessage rawChannels. */
    public rawChannels: number;

    /** FrameMessage tsInferEnd. */
    public tsInferEnd: number;

    /**
     * Creates a new FrameMessage instance using the specified properties.
     * @param [properties] Properties to set
     * @returns FrameMessage instance
     */
    public static create(properties?: IFrameMessage): FrameMessage;

    /**
     * Encodes the specified FrameMessage message. Does not implicitly {@link FrameMessage.verify|verify} messages.
     * @param message FrameMessage message or plain object to encode
     * @param [writer] Writer to encode to
     * @returns Writer
     */
    public static encode(message: IFrameMessage, writer?: $protobuf.Writer): $protobuf.Writer;

    /**
     * Encodes the specified FrameMessage message, length delimited. Does not implicitly {@link FrameMessage.verify|verify} messages.
     * @param message FrameMessage message or plain object to encode
     * @param [writer] Writer to encode to
     * @returns Writer
     */
    public static encodeDelimited(message: IFrameMessage, writer?: $protobuf.Writer): $protobuf.Writer;

    /**
     * Decodes a FrameMessage message from the specified reader or buffer.
     * @param reader Reader or buffer to decode from
     * @param [length] Message length if known beforehand
     * @returns FrameMessage
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    public static decode(reader: ($protobuf.Reader|Uint8Array), length?: number): FrameMessage;

    /**
     * Decodes a FrameMessage message from the specified reader or buffer, length delimited.
     * @param reader Reader or buffer to decode from
     * @returns FrameMessage
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    public static decodeDelimited(reader: ($protobuf.Reader|Uint8Array)): FrameMessage;

    /**
     * Verifies a FrameMessage message.
     * @param message Plain object to verify
     * @returns `null` if valid, otherwise the reason why it is not
     */
    public static verify(message: { [k: string]: any }): (string|null);

    /**
     * Creates a FrameMessage message from a plain object. Also converts values to their respective internal types.
     * @param object Plain object
     * @returns FrameMessage
     */
    public static fromObject(object: { [k: string]: any }): FrameMessage;

    /**
     * Creates a plain object from a FrameMessage message. Also converts values to other types if specified.
     * @param message FrameMessage
     * @param [options] Conversion options
     * @returns Plain object
     */
    public static toObject(message: FrameMessage, options?: $protobuf.IConversionOptions): { [k: string]: any };

    /**
     * Converts this FrameMessage to JSON.
     * @returns JSON object
     */
    public toJSON(): { [k: string]: any };

    /**
     * Gets the default type url for FrameMessage
     * @param [typeUrlPrefix] your custom typeUrlPrefix(default "type.googleapis.com")
     * @returns The default type url
     */
    public static getTypeUrl(typeUrlPrefix?: string): string;
}
