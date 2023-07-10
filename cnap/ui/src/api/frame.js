/*eslint-disable block-scoped-var, id-length, no-control-regex, no-magic-numbers, no-prototype-builtins, no-redeclare, no-shadow, no-var, sort-vars*/
import * as $protobuf from "protobufjs/minimal";

// Common aliases
const $Reader = $protobuf.Reader, $Writer = $protobuf.Writer, $util = $protobuf.util;

// Exported root namespace
const $root = $protobuf.roots["default"] || ($protobuf.roots["default"] = {});

export const FrameMessage = $root.FrameMessage = (() => {

    /**
     * Properties of a FrameMessage.
     * @exports IFrameMessage
     * @interface IFrameMessage
     * @property {string|null} [pipelineId] FrameMessage pipelineId
     * @property {number|Long|null} [sequence] FrameMessage sequence
     * @property {Uint8Array|null} [raw] FrameMessage raw
     * @property {number|null} [tsNew] FrameMessage tsNew
     * @property {number|null} [rawHeight] FrameMessage rawHeight
     * @property {number|null} [rawWidth] FrameMessage rawWidth
     * @property {number|null} [rawChannels] FrameMessage rawChannels
     * @property {number|null} [tsInferStart] FrameMessage tsInferStart
     */

    /**
     * Constructs a new FrameMessage.
     * @exports FrameMessage
     * @classdesc Represents a FrameMessage.
     * @implements IFrameMessage
     * @constructor
     * @param {IFrameMessage=} [properties] Properties to set
     */
    function FrameMessage(properties) {
        if (properties)
            for (let keys = Object.keys(properties), i = 0; i < keys.length; ++i)
                if (properties[keys[i]] != null)
                    this[keys[i]] = properties[keys[i]];
    }

    /**
     * FrameMessage pipelineId.
     * @member {string} pipelineId
     * @memberof FrameMessage
     * @instance
     */
    FrameMessage.prototype.pipelineId = "";

    /**
     * FrameMessage sequence.
     * @member {number|Long} sequence
     * @memberof FrameMessage
     * @instance
     */
    FrameMessage.prototype.sequence = $util.Long ? $util.Long.fromBits(0,0,false) : 0;

    /**
     * FrameMessage raw.
     * @member {Uint8Array} raw
     * @memberof FrameMessage
     * @instance
     */
    FrameMessage.prototype.raw = $util.newBuffer([]);

    /**
     * FrameMessage tsNew.
     * @member {number} tsNew
     * @memberof FrameMessage
     * @instance
     */
    FrameMessage.prototype.tsNew = 0;

    /**
     * FrameMessage rawHeight.
     * @member {number} rawHeight
     * @memberof FrameMessage
     * @instance
     */
    FrameMessage.prototype.rawHeight = 0;

    /**
     * FrameMessage rawWidth.
     * @member {number} rawWidth
     * @memberof FrameMessage
     * @instance
     */
    FrameMessage.prototype.rawWidth = 0;

    /**
     * FrameMessage rawChannels.
     * @member {number} rawChannels
     * @memberof FrameMessage
     * @instance
     */
    FrameMessage.prototype.rawChannels = 0;

    /**
     * FrameMessage tsInferStart.
     * @member {number} tsInferStart
     * @memberof FrameMessage
     * @instance
     */
    FrameMessage.prototype.tsInferStart = 0;

    /**
     * Creates a new FrameMessage instance using the specified properties.
     * @function create
     * @memberof FrameMessage
     * @static
     * @param {IFrameMessage=} [properties] Properties to set
     * @returns {FrameMessage} FrameMessage instance
     */
    FrameMessage.create = function create(properties) {
        return new FrameMessage(properties);
    };

    /**
     * Encodes the specified FrameMessage message. Does not implicitly {@link FrameMessage.verify|verify} messages.
     * @function encode
     * @memberof FrameMessage
     * @static
     * @param {IFrameMessage} message FrameMessage message or plain object to encode
     * @param {$protobuf.Writer} [writer] Writer to encode to
     * @returns {$protobuf.Writer} Writer
     */
    FrameMessage.encode = function encode(message, writer) {
        if (!writer)
            writer = $Writer.create();
        if (message.pipelineId != null && Object.hasOwnProperty.call(message, "pipelineId"))
            writer.uint32(/* id 1, wireType 2 =*/10).string(message.pipelineId);
        if (message.sequence != null && Object.hasOwnProperty.call(message, "sequence"))
            writer.uint32(/* id 2, wireType 0 =*/16).int64(message.sequence);
        if (message.raw != null && Object.hasOwnProperty.call(message, "raw"))
            writer.uint32(/* id 3, wireType 2 =*/26).bytes(message.raw);
        if (message.tsNew != null && Object.hasOwnProperty.call(message, "tsNew"))
            writer.uint32(/* id 4, wireType 1 =*/33).double(message.tsNew);
        if (message.rawHeight != null && Object.hasOwnProperty.call(message, "rawHeight"))
            writer.uint32(/* id 5, wireType 0 =*/40).int32(message.rawHeight);
        if (message.rawWidth != null && Object.hasOwnProperty.call(message, "rawWidth"))
            writer.uint32(/* id 6, wireType 0 =*/48).int32(message.rawWidth);
        if (message.rawChannels != null && Object.hasOwnProperty.call(message, "rawChannels"))
            writer.uint32(/* id 7, wireType 0 =*/56).int32(message.rawChannels);
        if (message.tsInferStart != null && Object.hasOwnProperty.call(message, "tsInferStart"))
            writer.uint32(/* id 8, wireType 1 =*/65).double(message.tsInferStart);
        return writer;
    };

    /**
     * Encodes the specified FrameMessage message, length delimited. Does not implicitly {@link FrameMessage.verify|verify} messages.
     * @function encodeDelimited
     * @memberof FrameMessage
     * @static
     * @param {IFrameMessage} message FrameMessage message or plain object to encode
     * @param {$protobuf.Writer} [writer] Writer to encode to
     * @returns {$protobuf.Writer} Writer
     */
    FrameMessage.encodeDelimited = function encodeDelimited(message, writer) {
        return this.encode(message, writer).ldelim();
    };

    /**
     * Decodes a FrameMessage message from the specified reader or buffer.
     * @function decode
     * @memberof FrameMessage
     * @static
     * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
     * @param {number} [length] Message length if known beforehand
     * @returns {FrameMessage} FrameMessage
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    FrameMessage.decode = function decode(reader, length) {
        if (!(reader instanceof $Reader))
            reader = $Reader.create(reader);
        let end = length === undefined ? reader.len : reader.pos + length, message = new $root.FrameMessage();
        while (reader.pos < end) {
            let tag = reader.uint32();
            switch (tag >>> 3) {
            case 1: {
                    message.pipelineId = reader.string();
                    break;
                }
            case 2: {
                    message.sequence = reader.int64();
                    break;
                }
            case 3: {
                    message.raw = reader.bytes();
                    break;
                }
            case 4: {
                    message.tsNew = reader.double();
                    break;
                }
            case 5: {
                    message.rawHeight = reader.int32();
                    break;
                }
            case 6: {
                    message.rawWidth = reader.int32();
                    break;
                }
            case 7: {
                    message.rawChannels = reader.int32();
                    break;
                }
            case 8: {
                    message.tsInferStart = reader.double();
                    break;
                }
            default:
                reader.skipType(tag & 7);
                break;
            }
        }
        return message;
    };

    /**
     * Decodes a FrameMessage message from the specified reader or buffer, length delimited.
     * @function decodeDelimited
     * @memberof FrameMessage
     * @static
     * @param {$protobuf.Reader|Uint8Array} reader Reader or buffer to decode from
     * @returns {FrameMessage} FrameMessage
     * @throws {Error} If the payload is not a reader or valid buffer
     * @throws {$protobuf.util.ProtocolError} If required fields are missing
     */
    FrameMessage.decodeDelimited = function decodeDelimited(reader) {
        if (!(reader instanceof $Reader))
            reader = new $Reader(reader);
        return this.decode(reader, reader.uint32());
    };

    /**
     * Verifies a FrameMessage message.
     * @function verify
     * @memberof FrameMessage
     * @static
     * @param {Object.<string,*>} message Plain object to verify
     * @returns {string|null} `null` if valid, otherwise the reason why it is not
     */
    FrameMessage.verify = function verify(message) {
        if (typeof message !== "object" || message === null)
            return "object expected";
        if (message.pipelineId != null && message.hasOwnProperty("pipelineId"))
            if (!$util.isString(message.pipelineId))
                return "pipelineId: string expected";
        if (message.sequence != null && message.hasOwnProperty("sequence"))
            if (!$util.isInteger(message.sequence) && !(message.sequence && $util.isInteger(message.sequence.low) && $util.isInteger(message.sequence.high)))
                return "sequence: integer|Long expected";
        if (message.raw != null && message.hasOwnProperty("raw"))
            if (!(message.raw && typeof message.raw.length === "number" || $util.isString(message.raw)))
                return "raw: buffer expected";
        if (message.tsNew != null && message.hasOwnProperty("tsNew"))
            if (typeof message.tsNew !== "number")
                return "tsNew: number expected";
        if (message.rawHeight != null && message.hasOwnProperty("rawHeight"))
            if (!$util.isInteger(message.rawHeight))
                return "rawHeight: integer expected";
        if (message.rawWidth != null && message.hasOwnProperty("rawWidth"))
            if (!$util.isInteger(message.rawWidth))
                return "rawWidth: integer expected";
        if (message.rawChannels != null && message.hasOwnProperty("rawChannels"))
            if (!$util.isInteger(message.rawChannels))
                return "rawChannels: integer expected";
        if (message.tsInferStart != null && message.hasOwnProperty("tsInferStart"))
            if (typeof message.tsInferStart !== "number")
                return "tsInferStart: number expected";
        return null;
    };

    /**
     * Creates a FrameMessage message from a plain object. Also converts values to their respective internal types.
     * @function fromObject
     * @memberof FrameMessage
     * @static
     * @param {Object.<string,*>} object Plain object
     * @returns {FrameMessage} FrameMessage
     */
    FrameMessage.fromObject = function fromObject(object) {
        if (object instanceof $root.FrameMessage)
            return object;
        let message = new $root.FrameMessage();
        if (object.pipelineId != null)
            message.pipelineId = String(object.pipelineId);
        if (object.sequence != null)
            if ($util.Long)
                (message.sequence = $util.Long.fromValue(object.sequence)).unsigned = false;
            else if (typeof object.sequence === "string")
                message.sequence = parseInt(object.sequence, 10);
            else if (typeof object.sequence === "number")
                message.sequence = object.sequence;
            else if (typeof object.sequence === "object")
                message.sequence = new $util.LongBits(object.sequence.low >>> 0, object.sequence.high >>> 0).toNumber();
        if (object.raw != null)
            if (typeof object.raw === "string")
                $util.base64.decode(object.raw, message.raw = $util.newBuffer($util.base64.length(object.raw)), 0);
            else if (object.raw.length >= 0)
                message.raw = object.raw;
        if (object.tsNew != null)
            message.tsNew = Number(object.tsNew);
        if (object.rawHeight != null)
            message.rawHeight = object.rawHeight | 0;
        if (object.rawWidth != null)
            message.rawWidth = object.rawWidth | 0;
        if (object.rawChannels != null)
            message.rawChannels = object.rawChannels | 0;
        if (object.tsInferStart != null)
            message.tsInferStart = Number(object.tsInferStart);
        return message;
    };

    /**
     * Creates a plain object from a FrameMessage message. Also converts values to other types if specified.
     * @function toObject
     * @memberof FrameMessage
     * @static
     * @param {FrameMessage} message FrameMessage
     * @param {$protobuf.IConversionOptions} [options] Conversion options
     * @returns {Object.<string,*>} Plain object
     */
    FrameMessage.toObject = function toObject(message, options) {
        if (!options)
            options = {};
        let object = {};
        if (options.defaults) {
            object.pipelineId = "";
            if ($util.Long) {
                let long = new $util.Long(0, 0, false);
                object.sequence = options.longs === String ? long.toString() : options.longs === Number ? long.toNumber() : long;
            } else
                object.sequence = options.longs === String ? "0" : 0;
            if (options.bytes === String)
                object.raw = "";
            else {
                object.raw = [];
                if (options.bytes !== Array)
                    object.raw = $util.newBuffer(object.raw);
            }
            object.tsNew = 0;
            object.rawHeight = 0;
            object.rawWidth = 0;
            object.rawChannels = 0;
            object.tsInferStart = 0;
        }
        if (message.pipelineId != null && message.hasOwnProperty("pipelineId"))
            object.pipelineId = message.pipelineId;
        if (message.sequence != null && message.hasOwnProperty("sequence"))
            if (typeof message.sequence === "number")
                object.sequence = options.longs === String ? String(message.sequence) : message.sequence;
            else
                object.sequence = options.longs === String ? $util.Long.prototype.toString.call(message.sequence) : options.longs === Number ? new $util.LongBits(message.sequence.low >>> 0, message.sequence.high >>> 0).toNumber() : message.sequence;
        if (message.raw != null && message.hasOwnProperty("raw"))
            object.raw = options.bytes === String ? $util.base64.encode(message.raw, 0, message.raw.length) : options.bytes === Array ? Array.prototype.slice.call(message.raw) : message.raw;
        if (message.tsNew != null && message.hasOwnProperty("tsNew"))
            object.tsNew = options.json && !isFinite(message.tsNew) ? String(message.tsNew) : message.tsNew;
        if (message.rawHeight != null && message.hasOwnProperty("rawHeight"))
            object.rawHeight = message.rawHeight;
        if (message.rawWidth != null && message.hasOwnProperty("rawWidth"))
            object.rawWidth = message.rawWidth;
        if (message.rawChannels != null && message.hasOwnProperty("rawChannels"))
            object.rawChannels = message.rawChannels;
        if (message.tsInferStart != null && message.hasOwnProperty("tsInferStart"))
            object.tsInferStart = options.json && !isFinite(message.tsInferStart) ? String(message.tsInferStart) : message.tsInferStart;
        return object;
    };

    /**
     * Converts this FrameMessage to JSON.
     * @function toJSON
     * @memberof FrameMessage
     * @instance
     * @returns {Object.<string,*>} JSON object
     */
    FrameMessage.prototype.toJSON = function toJSON() {
        return this.constructor.toObject(this, $protobuf.util.toJSONOptions);
    };

    /**
     * Gets the default type url for FrameMessage
     * @function getTypeUrl
     * @memberof FrameMessage
     * @static
     * @param {string} [typeUrlPrefix] your custom typeUrlPrefix(default "type.googleapis.com")
     * @returns {string} The default type url
     */
    FrameMessage.getTypeUrl = function getTypeUrl(typeUrlPrefix) {
        if (typeUrlPrefix === undefined) {
            typeUrlPrefix = "type.googleapis.com";
        }
        return typeUrlPrefix + "/FrameMessage";
    };

    return FrameMessage;
})();

export { $root as default };
