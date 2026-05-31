       IDENTIFICATION DIVISION.
       PROGRAM-ID. INVENTORY-MGMT.
       AUTHOR. LEGACY-SYSTEMS.
      *
      * Sistema de gestión de inventario legacy
      * Migración objetivo: Rust (seguridad de memoria)
      *
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-PRODUCT.
           05 PROD-CODE       PIC X(10).
           05 PROD-NAME       PIC X(50).
           05 PROD-QUANTITY   PIC 9(6).
           05 PROD-PRICE      PIC 9(7)V99.
           05 PROD-CATEGORY   PIC X(20).
       
       01 WS-TOTALS.
           05 TOTAL-PRODUCTS  PIC 9(6) VALUE 0.
           05 TOTAL-VALUE     PIC 9(12)V99 VALUE 0.
           05 LOW-STOCK-COUNT PIC 9(4) VALUE 0.
       
       01 WS-LOW-STOCK-LIMIT  PIC 9(4) VALUE 10.
       01 WS-SEARCH-CODE      PIC X(10).
       01 WS-FOUND-FLAG       PIC X(1) VALUE 'N'.
           88 PRODUCT-FOUND   VALUE 'Y'.
           88 PRODUCT-NOT-FOUND VALUE 'N'.

       PROCEDURE DIVISION.
       MAIN-PROGRAM.
           PERFORM INITIALIZE-INVENTORY
           PERFORM ADD-SAMPLE-PRODUCTS
           PERFORM CHECK-LOW-STOCK
           PERFORM DISPLAY-SUMMARY
           STOP RUN.

       INITIALIZE-INVENTORY.
           DISPLAY "=============================="
           DISPLAY "  SISTEMA DE INVENTARIO"
           DISPLAY "  Version Legacy COBOL"
           DISPLAY "=============================="
           MOVE 0 TO TOTAL-PRODUCTS
           MOVE 0 TO TOTAL-VALUE
           MOVE 0 TO LOW-STOCK-COUNT.

       ADD-SAMPLE-PRODUCTS.
           MOVE "PROD001" TO PROD-CODE
           MOVE "Laptop HP EliteBook" TO PROD-NAME
           MOVE 25 TO PROD-QUANTITY
           MOVE 3500.00 TO PROD-PRICE
           MOVE "Computadoras" TO PROD-CATEGORY
           PERFORM REGISTER-PRODUCT
           
           MOVE "PROD002" TO PROD-CODE
           MOVE "Mouse Logitech MX" TO PROD-NAME
           MOVE 150 TO PROD-QUANTITY
           MOVE 89.90 TO PROD-PRICE
           MOVE "Perifericos" TO PROD-CATEGORY
           PERFORM REGISTER-PRODUCT
           
           MOVE "PROD003" TO PROD-CODE
           MOVE "Monitor 27 4K" TO PROD-NAME
           MOVE 5 TO PROD-QUANTITY
           MOVE 1200.00 TO PROD-PRICE
           MOVE "Monitores" TO PROD-CATEGORY
           PERFORM REGISTER-PRODUCT.

       REGISTER-PRODUCT.
           ADD 1 TO TOTAL-PRODUCTS
           COMPUTE TOTAL-VALUE = TOTAL-VALUE + 
               (PROD-QUANTITY * PROD-PRICE)
           DISPLAY "  + Registrado: " PROD-NAME
           DISPLAY "    Codigo: " PROD-CODE
           DISPLAY "    Cantidad: " PROD-QUANTITY
           DISPLAY "    Precio: S/. " PROD-PRICE.

       CHECK-LOW-STOCK.
           DISPLAY " "
           DISPLAY "--- ALERTA STOCK BAJO ---"
           IF PROD-QUANTITY < WS-LOW-STOCK-LIMIT
               ADD 1 TO LOW-STOCK-COUNT
               DISPLAY "  ! BAJO STOCK: " PROD-NAME
               DISPLAY "    Solo quedan: " PROD-QUANTITY " unidades"
           ELSE
               DISPLAY "  Stock OK para ultimo producto verificado"
           END-IF.

       DISPLAY-SUMMARY.
           DISPLAY " "
           DISPLAY "=============================="
           DISPLAY "  RESUMEN DE INVENTARIO"
           DISPLAY "  Productos: " TOTAL-PRODUCTS
           DISPLAY "  Valor total: S/. " TOTAL-VALUE
           DISPLAY "  Alertas stock bajo: " LOW-STOCK-COUNT
           DISPLAY "==============================".
