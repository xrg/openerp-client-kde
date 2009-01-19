import net.sf.jasperreports.engine.JasperCompileManager;
import net.sf.jasperreports.engine.JasperFillManager;
import net.sf.jasperreports.engine.JasperExportManager;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.JasperPrint;
import net.sf.jasperreports.engine.util.JRLoader;
import net.sf.jasperreports.engine.data.JRXmlDataSource;
import net.sf.jasperreports.engine.util.JRXmlUtils;
import net.sf.jasperreports.engine.query.JRXPathQueryExecuterFactory;
import net.sf.jasperreports.engine.JRQuery;
import net.sf.jasperreports.view.JasperViewer;
import org.w3c.dom.Document;
import java.sql.*;
import java.util.*;
import java.io.FileInputStream;

public class ReportCreator {

	public static void createReport( String reportFile, String xmlFile, String reportOutput, Connection con , HashMap params )
	{
		try {
			JasperReport report;
			JRQuery query;
			JasperPrint jasperPrint=null;
			String subreportDir;
			int index;
			
			report = (JasperReport) JRLoader.loadObject( reportFile );
			query = report.getQuery();
			
			Map parameters = params;

			subreportDir = reportFile.substring( 0, reportFile.lastIndexOf('/') );
			index = reportFile.lastIndexOf('/');
			if ( index != -1 )
				parameters.put( "SUBREPORT_DIR", reportFile.substring( 0, index+1 ) );

			if( query.getLanguage().equalsIgnoreCase(  "XPATH")  ){
				JRXmlDataSource dataSource = new JRXmlDataSource( xmlFile, "/data/record" );
				dataSource.setDatePattern( "yyyy-MM-dd mm:hh:ss" );
				dataSource.setNumberPattern( "#######0.##" );
				dataSource.setLocale( Locale.ENGLISH );
				jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
			} else if(  query.getLanguage().equalsIgnoreCase( "SQL")  ) {
				jasperPrint = JasperFillManager.fillReport( report, parameters, con );
			}
			JasperExportManager.exportReportToPdfFile( jasperPrint, reportOutput );
		} catch (Exception e){
			e.printStackTrace();
			System.out.println( e.getMessage() );
		}
	}

	public static Connection getConnection(String dsn, String user, String password) 
		throws java.lang.ClassNotFoundException, java.sql.SQLException
	{
		Connection connection;
		Class.forName("org.postgresql.Driver");

		System.out.println("DSN: " + dsn);
		connection = DriverManager.getConnection( dsn, user, password );
		connection.setAutoCommit(false);
		return connection;
	}

	public static HashMap parseParams( String params ){
		HashMap parameters= new HashMap();
		System.out.println( "Params:" + params );
		String[] p = params.split(";");
		for( int j=0; j < p.length ; j++ ){
			System.out.println( p[j] );
			String[] map = p[j].split(":");
			parameters.put( map[0] , map[1] );
		}
		System.out.println( parameters );
		return parameters;
	}

	public static void main( String[] args ) 
	{
		for( int i=0;i< args.length; i++ )
			System.out.println( "arguments:" + args[i]);

		Connection con=null;
		HashMap parameters;

		if ( args.length >= 3 ) {  
			String dsn = args[3];
			String user=args[4];
			String password=args[5];
			String params = args[6];
			try {
				con = getConnection( dsn,user,password );
			} catch( Exception e ){
				e.printStackTrace();
			}
			parameters = parseParams( params );
			createReport( args[0], args[1], args[2] , con, parameters );
		} else
			System.out.println( "Three arguments needed." );
	}
}

