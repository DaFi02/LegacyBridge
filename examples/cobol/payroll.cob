       IDENTIFICATION DIVISION.
       PROGRAM-ID. EMPLOYEE-PAYROLL.
       AUTHOR. LEGACY-SYSTEMS.
       DATE-WRITTEN. 1995-03-15.
      *
      * Sistema de cálculo de nómina legacy
      * Empresa: TechCorp Peru
      *
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT EMPLOYEE-FILE ASSIGN TO 'EMPFILE.DAT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT REPORT-FILE ASSIGN TO 'PAYROLL.RPT'
               ORGANIZATION IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD EMPLOYEE-FILE.
       01 EMPLOYEE-RECORD.
           05 EMP-ID          PIC 9(6).
           05 EMP-NAME        PIC X(30).
           05 EMP-DEPT        PIC X(10).
           05 EMP-SALARY      PIC 9(7)V99.
           05 EMP-HOURS       PIC 9(3).
           05 EMP-STATUS      PIC X(1).

       FD REPORT-FILE.
       01 REPORT-LINE         PIC X(132).

       WORKING-STORAGE SECTION.
       01 WS-GROSS-PAY        PIC 9(9)V99.
       01 WS-TAX              PIC 9(7)V99.
       01 WS-NET-PAY          PIC 9(9)V99.
       01 WS-OVERTIME-HOURS   PIC 9(3).
       01 WS-OVERTIME-PAY     PIC 9(7)V99.
       01 WS-TAX-RATE         PIC 9V99 VALUE 0.30.
       01 WS-OVERTIME-RATE    PIC 9V99 VALUE 1.50.
       01 WS-STANDARD-HOURS   PIC 9(3) VALUE 160.
       01 WS-TOTAL-PAYROLL    PIC 9(12)V99 VALUE 0.
       01 WS-EMP-COUNT        PIC 9(5) VALUE 0.
       01 WS-EOF-FLAG         PIC X(1) VALUE 'N'.
           88 END-OF-FILE     VALUE 'Y'.

       PROCEDURE DIVISION.
       MAIN-PROGRAM.
           PERFORM INITIALIZE-PROCESS
           PERFORM PROCESS-EMPLOYEES UNTIL END-OF-FILE
           PERFORM FINALIZE-PROCESS
           STOP RUN.

       INITIALIZE-PROCESS.
           OPEN INPUT EMPLOYEE-FILE
           OPEN OUTPUT REPORT-FILE
           DISPLAY "==================================="
           DISPLAY "  SISTEMA DE NOMINA - TECHCORP"
           DISPLAY "==================================="
           READ EMPLOYEE-FILE
               AT END SET END-OF-FILE TO TRUE
           END-READ.

       PROCESS-EMPLOYEES.
           IF EMP-STATUS = 'A'
               PERFORM CALCULATE-PAY
               PERFORM GENERATE-REPORT-LINE
               ADD 1 TO WS-EMP-COUNT
               ADD WS-NET-PAY TO WS-TOTAL-PAYROLL
           END-IF
           READ EMPLOYEE-FILE
               AT END SET END-OF-FILE TO TRUE
           END-READ.

       CALCULATE-PAY.
           MOVE 0 TO WS-OVERTIME-PAY
           IF EMP-HOURS > WS-STANDARD-HOURS
               COMPUTE WS-OVERTIME-HOURS = 
                   EMP-HOURS - WS-STANDARD-HOURS
               COMPUTE WS-OVERTIME-PAY = 
                   WS-OVERTIME-HOURS * (EMP-SALARY / WS-STANDARD-HOURS)
                   * WS-OVERTIME-RATE
           END-IF
           COMPUTE WS-GROSS-PAY = EMP-SALARY + WS-OVERTIME-PAY
           COMPUTE WS-TAX = WS-GROSS-PAY * WS-TAX-RATE
           COMPUTE WS-NET-PAY = WS-GROSS-PAY - WS-TAX.

       GENERATE-REPORT-LINE.
           DISPLAY "Empleado: " EMP-NAME
           DISPLAY "  ID: " EMP-ID
           DISPLAY "  Depto: " EMP-DEPT
           DISPLAY "  Salario Bruto: S/. " WS-GROSS-PAY
           DISPLAY "  Impuesto: S/. " WS-TAX
           DISPLAY "  Pago Neto: S/. " WS-NET-PAY
           DISPLAY "-----------------------------------".

       FINALIZE-PROCESS.
           DISPLAY " "
           DISPLAY "==================================="
           DISPLAY "  RESUMEN DE NOMINA"
           DISPLAY "  Empleados procesados: " WS-EMP-COUNT
           DISPLAY "  Total nómina: S/. " WS-TOTAL-PAYROLL
           DISPLAY "==================================="
           CLOSE EMPLOYEE-FILE
           CLOSE REPORT-FILE.
