import java.io.*;
import java.nio.charset.StandardCharsets;
public class Hello {
    public static void main(String[] args) throws Exception {
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        byte[] b = new byte[4096];
        int n;
        while ((n = System.in.read(b)) >= 0) buf.write(b, 0, n);
        String s = buf.toString(StandardCharsets.UTF_8);
        String name = "world";
        int i = s.indexOf("\"name\"");
        if (i >= 0) {
            int q = s.indexOf('"', i + 6);
            int q2 = q >= 0 ? s.indexOf('"', q + 1) : -1;
            if (q >= 0 && q2 > q) name = s.substring(q + 1, q2);
        }
        System.out.print("{\"v\":1,\"ok\":true,\"result\":{\"arm\":\"hello-java\",\"lang\":\"java\",\"hello\":\"hello, " + name + "\"}}");
    }
}
