import net.sf.jasperreports.engine.JasperCompileManager;

public class I18nGetText {
	public static void main (String [] args) {
		if ( args.length != 1 ) {
			System.out.println( "Syntax: I18nGetText filename.jrxml" );
			System.exit(1);
		}
		String fileName = args[0];

		System.setProperty("jasper.reports.compiler.class", "I18nGroovyCompiler");

		try {
			JasperCompileManager.compileReport( fileName );
			System.out.println( I18nGroovyCompiler.lastGeneratedSourceCode );
		} catch (Exception e) {
			System.out.println( "Error compiling report: " + e.getMessage() );
		}
	}
}
