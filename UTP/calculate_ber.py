def calculate_ber(received_bits, transmitted_bits):
    error_count = 0
    for i in range(len(received_bits)):
        if received_bits[i] != transmitted_bits[i]:
            error_count += 1
            print("\033[91m", end="")  # Establece el color de salida en rojo
        else:
            print("\033[0m", end="")  # Restablece el color de salida a su valor predeterminado
        print(received_bits[i], end=" ")
    print("\033[0m")  # Restablece el color de salida a su valor predeterminado
    ber = error_count / len(transmitted_bits)
    return ber * 100  # Retorna el valor de BER en porcentaje

def main():
    print("\n\tBit Error Rate (BER)\n")
    transmitted_bits = input("\nIngrese los bits transmitidos (separados por espacios): ").split()
    received_bits = input("Ingrese los bits recibidos (separados por espacios): ").split()
    print("\nBits en error")

    ber = calculate_ber(received_bits, transmitted_bits)

    print("\nBits transmitidos:", transmitted_bits)
    print("Tasa de error de bits (BER): {:.2f}%".format(ber),"\n")  # Muestra el valor de BER con dos decimales

if __name__ == "__main__":
    main()