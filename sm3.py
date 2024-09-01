def sm3(s: str) -> str:
    """
    sm3密码杂凑计算函数，参数输入为长度小于2^64比特的消息串，返回由16进制字符串表示的256位杂凑值
    """

    # 初始值，用于确定压缩函数寄存器的状态
    V = 0x7380166f4914b2b9172442d7da8a0600a96f30bc163138aae38dee4db0fb0e4e

    # 算法中“字”定义为32位的比特串
    MAX_32 = 0xffffffff

    # 32位循环左移
    def lshift(x: int, i: int) -> int:
        return ((x << (i % 32)) & MAX_32) + (x >> (32 - i % 32))

    # 常量T，用于计算
    def T(j: int) -> int:
        if 0 <= j <= 15:
            return 0x79cc4519
        return 0x7a879d8a

    # 布尔函数FFj
    def FF(j: int, x: int, y: int, z: int) -> int:
        if 0 <= j <= 15:
            return x ^ y ^ z
        return (x & y) | (x & z) | (y & z)

    # 布尔函数GGj
    def GG(j: int, x: int, y: int, z: int) -> int:
        if 0 <= j <= 15:
            return x ^ y ^ z
        return (x & y) | (~x & z)

    # 置换函数P0
    def P0(x: int) -> int:
        return x ^ lshift(x, 9) ^ lshift(x, 17)

    # 置换函数P1
    def P1(x: int) -> int:
        return x ^ lshift(x, 15) ^ lshift(x, 23)

    # 消息填充函数，对长度为l(l < 2^64)比特的消息s，填充至长度为512比特的倍数
    def fill(s: str) -> str:
        v = 0
        for i in s:
            v <<= 8
            v += ord(i)
        msg = bin(v)[2:].zfill(len(s) * 8)
        k = (960 - len(msg) - 1) % 512
        return hex(int(msg + '1' + '0' * k + bin(len(msg))[2:].zfill(64), 2))[2:]

    m = fill(s)

    # 迭代过程
    for i in range(len(m) // 128):

        # 消息扩展
        Bi = m[i * 128: (i + 1) * 128]
        W = []
        for j in range(16):
            W.append(int(Bi[j * 8: (j + 1) * 8], 16))

        for j in range(16, 68):
            W.append(P1(W[j - 16] ^ W[j - 9] ^ lshift(W[j - 3], 15)) ^ lshift(W[j - 13], 7) ^ W[j - 6])
        W_ = []
        for j in range(64):
            W_.append(W[j] ^ W[j + 4])

        A, B, C, D, E, F, G, H = [V >> ((7 - i) * 32) & MAX_32 for i in range(8)]

        # 迭代计算
        for j in range(64):
            ss1 = lshift((lshift(A, 12) + E + lshift(T(j), j)) & MAX_32, 7)
            ss2 = ss1 ^ lshift(A, 12)
            tt1 = (FF(j, A, B, C) + D + ss2 + W_[j]) & MAX_32
            tt2 = (GG(j, E, F, G) + H + ss1 + W[j]) & MAX_32
            D = C
            C = lshift(B, 9)
            B = A
            A = tt1
            H = G
            G = lshift(F, 19)
            F = E
            E = P0(tt2)
        V ^= ((A << 224) + (B << 192) + (C << 160) + (D << 128) + (E << 96) + (F << 64) + (G << 32) + H)
    return hex(V)[2:].zfill(64)  # 返回256比特结果（16进制表示）


if __name__ == "__main__":
    print(sm3("abc"))
    print(sm3("abcd" * 16))