public class BinToHex {

  private static int input;

  // input logic
  public static boolean input () {
    try {
      input = System.in.read();
      if (input != -1) return true;
      else return false;
    } catch (Exception e) {
      System.out.println( "ERROR: couldn't read from the standard input!" );
      return false;
    }
  }

  // logic loop
  public static void main (String[] args) {

    while (input()) {
      System.out.print( "0x" );
      String hexString = Integer.toHexString(input);
      if (hexString.length()<2) System.out.print( "0" );
      System.out.println( hexString );
    }

  }

}
